package router

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"net/http/httputil"
	"runtime"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/mostlygeek/llama-swap/internal/config"
	"github.com/mostlygeek/llama-swap/internal/logmon"
	"github.com/mostlygeek/llama-swap/internal/shared"
)

type peerMember struct {
	peerID       string
	reverseProxy *httputil.ReverseProxy
	apiKey       string
}

type Peer struct {
	cfg    config.Config
	logger *logmon.Monitor
	peers  map[string]*peerMember
	health map[string]*PeerHealth

	shutdownCtx  context.Context
	shutdownFn   context.CancelFunc
	shuttingDown atomic.Bool
	inflight     sync.WaitGroup
}

func NewPeer(cfg config.Config, logger *logmon.Monitor) (*Peer, error) {
	peers := cfg.Peers
	modelMap := make(map[string]*peerMember)
	healthMap := make(map[string]*PeerHealth)

	peerIDs := make([]string, 0, len(peers))
	for peerID := range peers {
		peerIDs = append(peerIDs, peerID)
	}
	sort.Strings(peerIDs)

	for _, peerID := range peerIDs {
		peer := peers[peerID]

		peerTransport := &http.Transport{
			Proxy: http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   time.Duration(peer.Timeouts.Connect) * time.Second,
				KeepAlive: time.Duration(peer.Timeouts.KeepAlive) * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   time.Duration(peer.Timeouts.TLSHandshake) * time.Second,
			ResponseHeaderTimeout: time.Duration(peer.Timeouts.ResponseHeader) * time.Second,
			ExpectContinueTimeout: time.Duration(peer.Timeouts.ExpectContinue) * time.Second,
			ForceAttemptHTTP2:     true,
			MaxIdleConns:          100,
			MaxIdleConnsPerHost:   10,
			IdleConnTimeout:       time.Duration(peer.Timeouts.IdleConn) * time.Second,
		}

		reverseProxy := &httputil.ReverseProxy{
			Transport: peerTransport,
			Rewrite: func(r *httputil.ProxyRequest) {
				r.SetURL(peer.ProxyURL)
				r.Out.Host = r.Out.URL.Host
			},
		}

		reverseProxy.ModifyResponse = func(resp *http.Response) error {
			if resp.Request != nil {
				if obs := healthObserverFrom(resp.Request.Context()); obs != nil {
					obs.status = resp.StatusCode
					if resp.StatusCode < 200 || resp.StatusCode >= 300 {
						// Immediately classifiable; the body needs no observation.
						obs.finishStatus(resp.StatusCode)
					} else if resp.Body != nil {
						resp.Body = &observingReadCloser{ReadCloser: resp.Body, obs: obs}
					} else {
						obs.finishAtEOF()
					}
				}
			}
			if strings.Contains(strings.ToLower(resp.Header.Get("Content-Type")), "text/event-stream") {
				resp.Header.Set("X-Accel-Buffering", "no")
			}
			return nil
		}

		reverseProxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
			if obs := healthObserverFrom(r.Context()); obs != nil {
				obs.finishTransport(err)
			}
			logger.Warnf("peer %s: proxy error: %v", peerID, err)
			errMsg := fmt.Sprintf("peer proxy error: %v", err)
			if runtime.GOOS == "darwin" && strings.Contains(err.Error(), "connect: no route to host") {
				errMsg += " (hint: on macOS, check System Settings > Privacy & Security > Local Network permissions)"
			}
			http.Error(w, errMsg, http.StatusBadGateway)
		}

		hc := peer.Health
		hc.ApplyDefaults()
		if hc.Enabled != nil && *hc.Enabled {
			healthMap[peerID] = NewPeerHealth(peerID, hc, logger)
		}

		pp := &peerMember{
			peerID:       peerID,
			reverseProxy: reverseProxy,
			apiKey:       peer.ApiKey,
		}

		for _, modelID := range peer.Models {
			if _, found := modelMap[modelID]; found {
				logger.Warnf("peer %s: model %s already mapped to another peer, skipping", peerID, modelID)
				continue
			}
			modelMap[modelID] = pp
		}
	}

	shutdownCtx, shutdownFn := context.WithCancel(context.Background())

	return &Peer{
		cfg:         cfg,
		logger:      logger,
		peers:       modelMap,
		health:      healthMap,
		shutdownCtx: shutdownCtx,
		shutdownFn:  shutdownFn,
	}, nil
}

func (r *Peer) Handles(model string) bool {
	_, ok := r.peers[model]
	return ok
}

func (r *Peer) Shutdown(timeout time.Duration) error {
	if !r.shuttingDown.CompareAndSwap(false, true) {
		return fmt.Errorf("shutdown already in progress")
	}

	if timeout == 0 {
		r.shutdownFn()
		r.inflight.Wait()
		return nil
	}

	done := make(chan struct{})
	go func() {
		r.inflight.Wait()
		close(done)
	}()

	select {
	case <-done:
		return nil
	case <-time.After(timeout):
		r.shutdownFn()
		r.inflight.Wait()
		return fmt.Errorf("peer shutdown timed out after %v", timeout)
	}
}

func (r *Peer) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	if r.shuttingDown.Load() {
		shared.SendError(w, req, fmt.Errorf("peer proxy is shutting down"))
		return
	}
	r.inflight.Add(1)
	defer r.inflight.Done()

	data, err := shared.FetchContext(req, r.cfg)
	if err != nil {
		shared.SendError(w, req, err)
		return
	}

	pp, found := r.peers[data.ModelID]
	if !found {
		r.logger.Warnf("peer model not found: %s", data.ModelID)
		shared.SendError(w, req, ErrNoPeerModelFound)
		return
	}

	r.logger.Debugf("peer: routing model %s to peer %s", data.ModelID, pp.peerID)

	if pp.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+pp.apiKey)
		req.Header.Set("x-api-key", pp.apiKey)
	}

	// Cancel the proxy request when the client disconnects or shutdown times out.
	// AfterFunc links both parent contexts to our child without a goroutine leak.
	ctx, cancel := context.WithCancel(context.Background())
	stopReq := context.AfterFunc(req.Context(), cancel)
	stopShutdown := context.AfterFunc(r.shutdownCtx, cancel)
	req = req.WithContext(ctx)

	if ph, ok := r.health[pp.peerID]; ok {
		admit, probe, gen := ph.Admit()
		if !admit {
			stopShutdown()
			stopReq()
			cancel()
			r.serveCircuitOpen(w, pp.peerID, ph)
			return
		}
		req = req.WithContext(context.WithValue(ctx, healthObserverKey{}, newHealthObserver(ph, req, data.Streaming, probe, gen)))
	}

	pp.reverseProxy.ServeHTTP(w, req)

	stopShutdown()
	stopReq()
	cancel()
}

// serveCircuitOpen fails fast with a structured 503 when the peer's circuit is
// open. The peer is ejected from rotation; Retry-After hints when a half-open
// probe may be admitted.
func (r *Peer) serveCircuitOpen(w http.ResponseWriter, peerID string, ph *PeerHealth) {
	retryAfter := ph.RetryAfter()
	snap := ph.Snapshot()
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Retry-After", fmt.Sprintf("%d", int64(retryAfter/time.Second)+1))
	w.WriteHeader(http.StatusServiceUnavailable)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"error": map[string]any{
			"message":        fmt.Sprintf("peer %q circuit is open (failure score %.1f/%.1f); peer ejected from rotation", peerID, snap.FailureScore, snap.FailureThreshold),
			"type":           "peer_circuit_open",
			"code":           "peer_circuit_open",
			"peer":           peerID,
			"retry_after_ms": int64(retryAfter / time.Millisecond),
		},
	})
}

// HealthSnapshots returns the per-peer health view served by /peer-health,
// sorted by peer ID. The health map is built once in NewPeer and read-only
// afterwards, so no lock is needed.
func (r *Peer) HealthSnapshots() []HealthSnapshot {
	snaps := make([]HealthSnapshot, 0, len(r.health))
	for _, h := range r.health {
		snaps = append(snaps, h.Snapshot())
	}
	sort.Slice(snaps, func(i, j int) bool { return snaps[i].Peer < snaps[j].Peer })
	return snaps
}
