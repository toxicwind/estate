//! Fleet agent roster, per-agent history, and the live event-driven WS feed.
//!
//! Parses Squawk fleet message files (YAML frontmatter + markdown body) from
//! the shingle fleet directory. The WS feed is driven by a `notify` watcher
//! (inotify) that fans out new-message frames to every connected client --
//! no polling anywhere on this path.

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Path,
    },
    response::IntoResponse,
    Json,
};
use serde::Serialize;
use std::collections::HashMap;
use std::path::Path as FsPath;
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;

const FLEET_DIR: &str = "/home/toxic/shingle/squawk-root/fleet";
const FLEET_DIR_FALLBACK: &str = "/home/toxic/.shingle/squawk-root/fleet";

#[derive(Debug, Clone, Serialize)]
pub struct AgentCard {
    pub name: String,
    pub messages: usize,
    pub last_unix: i64,
    pub last_ts: String,
    pub status: String,
    pub last_title: String,
    pub last_seq: u64,
}

#[derive(Debug, Clone, Serialize)]
pub struct FleetMsg {
    pub seq: u64,
    pub from: String,
    pub to: String,
    pub ts: String,
    pub title: String,
    pub body: String,
    pub unix: i64,
}

fn fleet_dir() -> &'static str {
    if FsPath::new(FLEET_DIR).is_dir() {
        FLEET_DIR
    } else {
        FLEET_DIR_FALLBACK
    }
}

/// Parse one squawk fleet message file. Uses file mtime as the activity
/// timestamp (arrival time), which is what the roster status heuristic needs.
pub fn parse_fleet_msg(path: &FsPath) -> Option<FleetMsg> {
    let name = path.file_name()?.to_str()?;
    if !name.ends_with(".md") {
        return None;
    }
    let file_seq: u64 = name.split('-').next()?.parse().ok()?;
    let content = std::fs::read_to_string(path).ok()?;
    let mtime = std::fs::metadata(path).ok()?.modified().ok()?;
    let unix = mtime.duration_since(UNIX_EPOCH).ok()?.as_secs() as i64;

    let mut seq = file_seq;
    let mut from = String::new();
    let mut to = String::new();
    let mut ts = String::new();
    let mut title = String::new();
    let mut body = content.clone();

    let mut lines = content.lines();
    if lines.next().map(|l| l.trim()) == Some("---") {
        let mut fm: HashMap<String, String> = HashMap::new();
        let mut rest: Vec<&str> = Vec::new();
        let mut in_fm = true;
        for line in lines {
            if in_fm {
                if line.trim() == "---" {
                    in_fm = false;
                    continue;
                }
                if let Some(i) = line.find(':') {
                    fm.insert(
                        line[..i].trim().to_string(),
                        line[i + 1..].trim().to_string(),
                    );
                }
            } else {
                rest.push(line);
            }
        }
        if !in_fm {
            if let Some(s) = fm.get("seq").and_then(|v| v.parse::<u64>().ok()) {
                seq = s;
            }
            from = fm.get("from").cloned().unwrap_or_default();
            to = fm.get("to").cloned().unwrap_or_default();
            ts = fm.get("ts").cloned().unwrap_or_default();
            title = fm.get("title").cloned().unwrap_or_default();
            body = rest.join("\n").trim().to_string();
        }
    }
    if from.is_empty() {
        let parts: Vec<&str> = name.trim_end_matches(".md").split('-').collect();
        if parts.len() >= 3 {
            from = parts[1].to_string();
        }
    }
    if from.is_empty() {
        return None;
    }
    Some(FleetMsg {
        seq,
        from,
        to,
        ts,
        title,
        body,
        unix,
    })
}

fn status_for(last_unix: i64, now: i64) -> &'static str {
    let age = now - last_unix;
    if age < 300 {
        "active"
    } else if age < 1800 {
        "idle"
    } else if age < 7200 {
        "quiet"
    } else {
        "stale"
    }
}

fn agent_ok(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 64
        && name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
}

pub fn build_roster() -> Vec<AgentCard> {
    let mut map: HashMap<String, Vec<FleetMsg>> = HashMap::new();
    if let Ok(rd) = std::fs::read_dir(fleet_dir()) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("md") {
                continue;
            }
            if let Some(m) = parse_fleet_msg(&p) {
                map.entry(m.from.clone()).or_default().push(m);
            }
        }
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    let mut cards: Vec<AgentCard> = map
        .into_iter()
        .map(|(name, mut msgs)| {
            msgs.sort_by(|a, b| b.unix.cmp(&a.unix));
            let last = &msgs[0];
            AgentCard {
                name,
                messages: msgs.len(),
                last_unix: last.unix,
                last_ts: last.ts.clone(),
                status: status_for(last.unix, now).to_string(),
                last_title: last.title.clone(),
                last_seq: last.seq,
            }
        })
        .collect();
    cards.sort_by(|a, b| b.last_unix.cmp(&a.last_unix));
    cards
}

/// GET /api/agents/roster -- one card per agent, most-recently-active first.
pub async fn roster() -> Json<Vec<AgentCard>> {
    Json(build_roster())
}

/// GET /api/agents/:name -- drill-down: newest 200 messages from one agent.
pub async fn agent_history(Path(name): Path<String>) -> impl IntoResponse {
    if !agent_ok(&name) {
        return (
            axum::http::StatusCode::BAD_REQUEST,
            Json(serde_json::json!({"error": "invalid_name"})),
        )
            .into_response();
    }
    let mut msgs: Vec<FleetMsg> = Vec::new();
    if let Ok(rd) = std::fs::read_dir(fleet_dir()) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("md") {
                continue;
            }
            if let Some(m) = parse_fleet_msg(&p) {
                if m.from == name {
                    msgs.push(m);
                }
            }
        }
    }
    msgs.sort_by(|a, b| b.seq.cmp(&a.seq));
    let total = msgs.len();
    msgs.truncate(200);
    Json(serde_json::json!({"agent": name, "count": total, "messages": msgs})).into_response()
}

// ---------------------------------------------------------------------------
// Live WS feed: notify watcher -> broadcast -> every connected dashboard.
// ---------------------------------------------------------------------------

static BROADCAST: OnceLock<broadcast::Sender<String>> = OnceLock::new();

fn broadcaster() -> broadcast::Sender<String> {
    BROADCAST
        .get_or_init(|| {
            let (btx, _) = broadcast::channel::<String>(512);
            let tx = btx.clone();
            std::thread::spawn(move || watch_loop(tx));
            btx
        })
        .clone()
}

/// Start the fleet watcher early so no message is missed at boot.
pub fn init_fleet_feed() {
    broadcaster();
}

fn watch_loop(btx: broadcast::Sender<String>) {
    use notify::{recommended_watcher, EventKind, RecursiveMode, Watcher};
    let dir = fleet_dir().to_string();
    let (etx, erx) = std::sync::mpsc::channel::<std::path::PathBuf>();
    let mut watcher = match recommended_watcher(move |res: Result<notify::Event, notify::Error>| {
        if let Ok(ev) = res {
            // Create covers new files AND renames into the dir (inotify
            // MOVED_TO). Any Modify covers content writes; the Modify event
            // is queued by write(2) itself, so the content is present when
            // we read — no settle delay needed. (This mirrors squawk's own
            // inotifywait -e close_write/-e moved_to/-e create usage.)
            let interesting = match ev.kind {
                EventKind::Create(_) => true,
                EventKind::Modify(_) => true,
                _ => false,
            };
            if interesting {
                for p in ev.paths {
                    if p.extension().and_then(|x| x.to_str()) == Some("md") {
                        let _ = etx.send(p);
                    }
                }
            }
        }
    }) {
        Ok(w) => w,
        Err(e) => {
            eprintln!("[fleet-feed] watcher failed: {e}");
            return;
        }
    };
    if watcher
        .watch(FsPath::new(&dir), RecursiveMode::NonRecursive)
        .is_err()
    {
        return;
    }
    // seq -> best completeness broadcast so far. A file can raise Create
    // (empty, before the writer's first write) then Modify(Data) with the
    // full content; a writer doing several writes can also raise multiple
    // Modifies. We broadcast the most complete parse seen, upgrading if a
    // later event carries more content. Completeness = from+title+body bytes.
    let mut seen: HashMap<u64, usize> = HashMap::new();
    while let Ok(path) = erx.recv() {
        // No artificial settle delay: the Modify event is queued by the
        // write(2) syscall itself, so content is present when we read. An
        // empty file means Create won the race with the writer's first
        // write — skip it; the following Modify re-triggers this path.
        let size = std::fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
        if size == 0 {
            continue;
        }
        if let Some(m) = parse_fleet_msg(&path) {
            let completeness = m.from.len() + m.title.len() + m.body.len();
            let best = seen.get(&m.seq).copied().unwrap_or(0);
            // Always broadcast the first parse; upgrade only on strictly
            // more complete content (avoids duplicate frames for identical
            // re-notifies).
            if best > 0 && completeness <= best {
                continue;
            }
            seen.insert(m.seq, completeness);
            // Bound the map; eviction is approximate (seqs rise over time).
            if seen.len() > 8192 {
                let cutoff = m.seq.saturating_sub(8192);
                seen.retain(|&s, _| s >= cutoff);
            }
            let frame =
                serde_json::json!({"type": "squawk", "channel": "fleet", "message": m}).to_string();
            let _ = btx.send(frame);
            // Refresh the author's card so the roster grid updates live.
            if let Some(card) = build_roster().into_iter().find(|c| c.name == m.from) {
                let frame2 = serde_json::json!({"type": "agent", "agent": card}).to_string();
                let _ = btx.send(frame2);
            }
        }
    }
}

/// WS /ws/fleet -- hello frame on connect, squawk/agent frames on new
/// messages, ping every 30s as a keepalive. Clients reconnect with backoff.
/// Newest fleet messages, newest-first. Used for the fleet:init snapshot.
fn recent_messages(limit: usize) -> Vec<FleetMsg> {
    let mut msgs: Vec<FleetMsg> = Vec::new();
    if let Ok(rd) = std::fs::read_dir(fleet_dir()) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) != Some("md") {
                continue;
            }
            if let Some(m) = parse_fleet_msg(&p) {
                msgs.push(m);
            }
        }
    }
    msgs.sort_by(|a, b| b.seq.cmp(&a.seq));
    msgs.truncate(limit);
    msgs
}

/// Snapshot sent right after hello: full roster + recent messages so a new
/// client paints instantly without any HTTP round-trip.
fn init_frame() -> String {
    serde_json::json!({
        "type": "fleet:init",
        "roster": build_roster(),
        "messages": recent_messages(50),
    })
    .to_string()
}

pub async fn ws_fleet(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    let tx = broadcaster();
    let mut rx = tx.subscribe();
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let hello = serde_json::json!({
        "type": "hello",
        "ts": now,
        "roster_url": "/api/agents/roster",
    })
    .to_string();
    if socket.send(Message::Text(hello.into())).await.is_err() {
        return;
    }
    // Snapshot immediately after hello: the client paints roster + recent
    // messages from this frame, no HTTP needed.
    if socket
        .send(Message::Text(init_frame().into()))
        .await
        .is_err()
    {
        return;
    }
    // Purely event-driven: this task only wakes on broadcast frames or
    // socket input. No heartbeat timer.
    loop {
        tokio::select! {
            msg = socket.recv() => {
                match msg {
                    Some(Ok(Message::Close(_))) | None => break,
                    Some(Ok(Message::Ping(d))) => {
                        if socket.send(Message::Pong(d)).await.is_err() { break; }
                    }
                    _ => {}
                }
            }
            frame = rx.recv() => {
                match frame {
                    Ok(text) => {
                        if socket.send(Message::Text(text.into())).await.is_err() { break; }
                    }
                    Err(broadcast::error::RecvError::Lagged(_)) => continue,
                    Err(_) => break,
                }
            }
        }
    }
}
