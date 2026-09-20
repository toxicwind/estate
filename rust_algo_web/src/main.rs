mod agents;
mod fleet;
mod gpu;
mod watchdog;

use axum::{
    extract::{Path, Query},
    response::IntoResponse,
    routing::{any, get},
    Json, Router,
};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::time::Duration;
use tower_http::services::{ServeDir, ServeFile};

#[derive(Serialize)]
struct Health {
    status: String,
    model: Option<String>,
}

#[derive(Serialize, Deserialize)]
struct StatusResponse {
    online: bool,
    port: u16,
}

#[derive(Serialize, Deserialize)]
#[allow(non_snake_case)]
struct TelemetryResponse {
    aiEngine: String,
    gpuName: String,
    vramStr: String,
    cpuName: String,
    ramGb: u32,
}

#[derive(Deserialize)]
struct LlamaModel {
    id: String,
    status: LlamaModelStatus,
}

#[derive(Deserialize)]
struct LlamaModelStatus {
    value: String,
}

#[derive(Deserialize)]
struct LlamaModelsList {
    data: Vec<LlamaModel>,
}

#[derive(Serialize, Deserialize)]
struct ModelMetaResponse {
    id: String,
    context: String,
    fork: String,
    quant: String,
    vram: String,
    note: String,
    warning: String,
    active: bool,
    priority: u32,
}

#[derive(Serialize)]
struct ArchLiveResponse {
    services: HashMap<String, StatusResponse>,
    active_model: String,
    active_fork: String,
    models_by_fork: HashMap<String, u32>,
}

#[derive(Serialize)]
struct IntegrationProbe {
    name: String,
    url: String,
    online: bool,
    detail: String,
}

#[derive(Serialize)]
struct IntegrationsResponse {
    llama_swap: IntegrationProbe,
    chat_ui: String,
    hf_downloader: IntegrationProbe,
    fleet_last: Option<serde_json::Value>,
    forks: Option<serde_json::Value>,
    notes: Vec<String>,
}

async fn probe_url(name: &str, url: &str, path_hint: &str) -> IntegrationProbe {
    let cl = Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .unwrap_or_else(|_| Client::new());
    match cl.get(url).send().await {
        Ok(resp) => IntegrationProbe {
            name: name.into(),
            url: url.into(),
            online: resp.status().is_success() || resp.status().as_u16() == 302,
            detail: format!("{} status={}", path_hint, resp.status()),
        },
        Err(e) => IntegrationProbe {
            name: name.into(),
            url: url.into(),
            online: false,
            detail: format!("error: {e}"),
        },
    }
}

fn swap_base_url() -> String {
    // Prefer explicit swap port (LLAMA_SWAP_PORT / 25100).
    if let Ok(p) = std::env::var("LLAMA_SWAP_PORT") {
        return format!("http://127.0.0.1:{p}");
    }
    if let Ok(u) = std::env::var("LLM_PROXY_URL") {
        if u.contains(":25100") {
            return u.trim_end_matches('/').to_string();
        }
    }
    "http://127.0.0.1:25100".into()
}

async fn get_integrations() -> Json<IntegrationsResponse> {
    let swap_base = swap_base_url();
    let hf_port = std::env::var("HF_DOWNLOADER_PORT").unwrap_or_else(|_| "25106".into());
    let hf_url = format!("http://127.0.0.1:{hf_port}/api/health");
    let swap_health = format!("{}/health", swap_base.trim_end_matches('/'));

    let llama_swap = probe_url("llama-swap", &swap_health, "/health").await;
    let hf_downloader = probe_url("hf-downloader", &hf_url, "/api/health").await;

    let fleet_last = std::fs::read_to_string(
        "/home/toxic/sovereign/tools/fleet/results/bench-forks-latest.json",
    )
    .ok()
    .and_then(|s| serde_json::from_str(&s).ok());

    let forks = std::fs::read_to_string("/home/toxic/sovereign/tools/fleet/forks.json")
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok());

    Json(IntegrationsResponse {
        llama_swap,
        chat_ui: format!("{}/ui/", swap_base.trim_end_matches('/')),
        hf_downloader,
        fleet_last,
        forks,
        notes: vec![
            "Chat UI is llama-swap /ui — not this dashboard".into(),
            "LD paths for 4 forks live in tools/llama-swap/config.yaml macros (*_ld)".into(),
            "Fleet bench: tools/fleet/bench-forks.sh (graduated ctx; no 27B max first)".into(),
        ],
    })
}

// ---------- Squawk feed ----------
const SQUAWK_ROOT: &str = "/home/toxic/.shingle/squawk-root";

#[derive(Serialize)]
struct SquawkMessage {
    seq: u64,
    from: String,
    to: String,
    ts: String,
    title: String,
    body: String,
}

fn squawk_channel_ok(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 64
        && name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
}

fn parse_squawk_message(path: &std::path::Path) -> Option<SquawkMessage> {
    let name = path.file_name()?.to_str()?;
    let file_seq: u64 = name.split('-').next()?.parse().ok()?;
    let content = std::fs::read_to_string(path).ok()?;
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
    Some(SquawkMessage {
        seq,
        from,
        to,
        ts,
        title,
        body,
    })
}

async fn get_squawk_channels() -> Json<Vec<String>> {
    let mut chans = Vec::new();
    if let Ok(rd) = std::fs::read_dir(SQUAWK_ROOT) {
        for e in rd.flatten() {
            if e.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                if let Some(n) = e.file_name().to_str() {
                    if squawk_channel_ok(n) {
                        let has_md = std::fs::read_dir(e.path())
                            .map(|rd| {
                                rd.flatten().any(|f| {
                                    f.path().extension().and_then(|x| x.to_str()) == Some("md")
                                })
                            })
                            .unwrap_or(false);
                        if has_md {
                            chans.push(n.to_string());
                        }
                    }
                }
            }
        }
    }
    chans.sort();
    Json(chans)
}

async fn get_squawk_channel(
    Path(channel): Path<String>,
    Query(q): Query<HashMap<String, String>>,
) -> impl IntoResponse {
    if !squawk_channel_ok(&channel) {
        return (
            axum::http::StatusCode::BAD_REQUEST,
            Json(serde_json::json!({"error": "invalid_channel"})),
        )
            .into_response();
    }
    let limit: usize = q
        .get("limit")
        .and_then(|v| v.parse().ok())
        .unwrap_or(50)
        .clamp(1, 200);
    let dir = std::path::Path::new(SQUAWK_ROOT).join(&channel);
    let mut msgs: Vec<SquawkMessage> = Vec::new();
    if let Ok(rd) = std::fs::read_dir(&dir) {
        for e in rd.flatten() {
            let p = e.path();
            if p.extension().and_then(|x| x.to_str()) == Some("md") {
                if let Some(m) = parse_squawk_message(&p) {
                    msgs.push(m);
                }
            }
        }
    }
    msgs.sort_by(|a, b| b.seq.cmp(&a.seq));
    let max_seq = msgs.first().map(|m| m.seq).unwrap_or(0);
    let total = msgs.len();
    msgs.truncate(limit);
    Json(serde_json::json!({
        "channel": channel,
        "seq": max_seq,
        "count": total,
        "messages": msgs,
    }))
    .into_response()
}

async fn get_fleet_last() -> Json<serde_json::Value> {
    let path = "/home/toxic/sovereign/tools/fleet/results/bench-forks-latest.json";
    match std::fs::read_to_string(path) {
        Ok(s) => Json(serde_json::from_str(&s).unwrap_or(serde_json::json!({"raw": s}))),
        Err(_) => Json(serde_json::json!({
            "status": "empty",
            "hint": "run: bash tools/fleet/bench-forks.sh"
        })),
    }
}

async fn health() -> Json<Health> {
    let m = std::env::var("LLM_PROXY_URL")
        .ok()
        .map(|u| format!("via {}", u));
    Json(Health {
        status: "ok".into(),
        model: m,
    })
}

async fn get_logs() -> Json<Vec<String>> {
    let mut logs = Vec::new();

    if let Ok(content) = std::fs::read_to_string("/home/toxic/sovereign/.state/logs/llama-swap.log")
    {
        let lines: Vec<&str> = content.lines().collect();
        let start = if lines.len() > 15 {
            lines.len() - 15
        } else {
            0
        };
        for line in &lines[start..] {
            if let Ok(val) = serde_json::from_str::<serde_json::Value>(line) {
                if let Some(msg) = val["message"].as_str() {
                    if !msg.contains("slot print_timing") && !msg.contains("srv  update_slots") {
                        logs.push(format!("[LlamaSwap] {}", msg));
                    }
                }
            } else {
                logs.push(format!("[LlamaSwap] {}", line));
            }
        }
    }

    logs.push("[Watchdog] Direct monitoring thread active on port 25104".to_string());
    logs.push("[System] Live architecture dashboard active".to_string());

    Json(logs)
}

async fn get_status() -> Json<HashMap<String, StatusResponse>> {
    let mut map = HashMap::new();
    let cl = Client::new();
    let pc_res = cl.get("http://127.0.0.1:25108/processes").send().await;

    let mut pc_running = Vec::new();
    if let Ok(resp) = pc_res {
        if let Ok(v) = resp.json::<serde_json::Value>().await {
            if let Some(arr) = v["data"].as_array() {
                for item in arr {
                    if let (Some(name), Some(running)) =
                        (item["name"].as_str(), item["is_running"].as_bool())
                    {
                        pc_running.push((name.to_string(), running));
                    }
                }
            }
        }
    }

    if pc_running.is_empty() {
        let defaults = vec![
            ("Llama Swap", "llama-swap", 25100),
            ("OpenFang Core", "openfang", 25103),
            ("Ouroboros", "rust-web", 25101),
            ("Prometheus", "prometheus", 25105),
            ("HF Downloader", "hf-downloader", 25106),
            ("Yote Status", "yote", 25102),
        ];
        for (ui_name, _, port) in defaults {
            let online = tokio::net::TcpStream::connect(format!("127.0.0.1:{}", port))
                .await
                .is_ok();
            map.insert(ui_name.to_string(), StatusResponse { online, port });
        }
    } else {
        for (name, is_running) in pc_running {
            let ui_name = match name.as_str() {
                "llama-swap" => "Llama Swap",
                "openfang" => "OpenFang Core",
                "rust-web" => "Ouroboros",
                "prometheus" => "Prometheus",
                "hf-downloader" => "HF Downloader",
                "yote" => "Yote Status",
                "safeneuron_steer" => "SafeNeuron Steer",
                "decoy_proxy" => "Decoy Proxy",
                "fleet_bench" => "Fleet Bench",
                _ => &name,
            };
            let port = match name.as_str() {
                "llama-swap" => 25100,
                "openfang" => 25103,
                "rust-web" => 25101,
                "prometheus" => 25105,
                "hf-downloader" => 25106,
                "yote" => 25102,
                "safeneuron_steer" => 25201,
                "decoy_proxy" => 25202,
                "fleet_bench" => 25203,
                _ => 0,
            };
            map.insert(
                ui_name.to_string(),
                StatusResponse {
                    online: is_running,
                    port,
                },
            );
        }
    }

    let watchdog_port = std::env::var("WATCHDOG_PORT")
        .ok()
        .and_then(|x| x.parse().ok())
        .unwrap_or(25104);
    let watchdog_online = cl
        .get(format!("http://127.0.0.1:{}/health", watchdog_port))
        .send()
        .await
        .is_ok();
    map.insert(
        "Watchdog".to_string(),
        StatusResponse {
            online: watchdog_online,
            port: watchdog_port,
        },
    );

    Json(map)
}

async fn get_telemetry() -> Json<TelemetryResponse> {
    let mut model_name = "Offline".to_string();
    let cl = Client::new();
    if let Ok(resp) = cl.get("http://127.0.0.1:25100/v1/models").send().await {
        if let Ok(val) = resp.json::<LlamaModelsList>().await {
            for m in val.data {
                if m.status.value != "unloaded" {
                    model_name = m.id;
                    break;
                }
            }
        }
    }

    Json(TelemetryResponse {
        aiEngine: model_name,
        gpuName: "NVIDIA GeForce RTX 3090".into(),
        vramStr: "24GB GDDR6X VRAM".into(),
        cpuName: "AMD Ryzen 7 8700F".into(),
        ramGb: 64,
    })
}

fn get_model_priorities() -> HashMap<String, u32> {
    let mut map = HashMap::new();
    if let Ok(content) =
        std::fs::read_to_string("/home/toxic/sovereign/tools/llama-swap/config.yaml")
    {
        let mut in_priority = false;
        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with("priority:") {
                in_priority = true;
                continue;
            }
            if in_priority {
                let indent = line.len() - line.trim_start().len();
                if indent < 8 && !trimmed.starts_with("#") && !trimmed.is_empty() {
                    in_priority = false;
                    continue;
                }
                if trimmed.starts_with("#") || trimmed.is_empty() {
                    continue;
                }
                if let Some(pos) = trimmed.find(':') {
                    let key = trimmed[..pos].trim().replace("\"", "");
                    let val_str = trimmed[pos + 1..].trim();
                    if let Ok(val) = val_str.parse::<u32>() {
                        map.insert(key, val);
                    }
                }
            }
        }
    }
    map
}

async fn get_models_meta() -> Json<Vec<ModelMetaResponse>> {
    let mut list = Vec::new();
    let cl = Client::new();
    let priorities = get_model_priorities();
    if let Ok(resp) = cl.get("http://127.0.0.1:25100/v1/models").send().await {
        if let Ok(val) = resp.json::<serde_json::Value>().await {
            if let Some(arr) = val["data"].as_array() {
                for m in arr {
                    let id = m["id"].as_str().unwrap_or("").to_string();
                    let active = m["status"]["value"].as_str().unwrap_or("") != "unloaded";
                    let meta = &m["meta"]["llamaswap"];

                    let context = match meta["context"].as_u64() {
                        Some(ctx) => format!("{}k", ctx / 1024),
                        None => "Default".to_string(),
                    };
                    let fork = meta["fork"]
                        .as_str()
                        .unwrap_or_else(|| id.split('/').next().unwrap_or("unknown"))
                        .to_string();
                    let quant = meta["quant"].as_str().unwrap_or("Unknown").to_string();
                    let vram = meta["vram"].as_str().unwrap_or("N/A").to_string();
                    let note = meta["note"].as_str().unwrap_or("").to_string();
                    let warning = meta["warning"].as_str().unwrap_or("").to_string();
                    let priority = *priorities.get(&id).unwrap_or(&0);

                    list.push(ModelMetaResponse {
                        id,
                        context,
                        fork,
                        quant,
                        vram,
                        note,
                        warning,
                        active,
                        priority,
                    });
                }
            }
        }
    }
    Json(list)
}

/// Live overlay for architecture.html: services + active model/fork tallies
async fn get_gpu_metrics() -> impl IntoResponse {
    match gpu::fetch_gpu_metrics().await {
        Ok(metrics) => {
            let rendered = gpu::render_prometheus_metrics(&metrics);
            (axum::http::StatusCode::OK, rendered)
        }
        Err(e) => (
            axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            format!("Error: {}", e),
        ),
    }
}

async fn get_arch_live() -> Json<ArchLiveResponse> {
    let status = get_status().await.0;
    let models = get_models_meta().await.0;

    let mut active_model = "Offline".to_string();
    let mut active_fork = "—".to_string();
    let mut models_by_fork: HashMap<String, u32> = HashMap::new();

    for m in &models {
        *models_by_fork.entry(m.fork.clone()).or_insert(0) += 1;
        if m.active {
            active_model = m.id.clone();
            active_fork = m.fork.clone();
        }
    }

    Json(ArchLiveResponse {
        services: status,
        active_model,
        active_fork,
        models_by_fork,
    })
}

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();

    let watchdog_port: u16 = std::env::var("WATCHDOG_PORT")
        .ok()
        .and_then(|x| x.parse().ok())
        .unwrap_or(25104);
    tokio::spawn(async move {
        watchdog::run(watchdog_port).await;
    });

    let s = ServeDir::new("static");
    // Fleet agent backend: notify-driven roster/history/live WS feed.
    agents::init_fleet_feed();
    // Built herd/mesh UIs (Svelte). SPA fallback to index.html.
    let herd_ui = ServeDir::new("static/herd-ui")
        .not_found_service(ServeFile::new("static/herd-ui/index.html"));
    let mesh_ui = ServeDir::new("static/mesh-ui")
        .not_found_service(ServeFile::new("static/mesh-ui/index.html"));
    // GHAS mesh (20 features) — thin native surface; full catalog also on mesh-hub :25115
    async fn mesh_features() -> impl IntoResponse {
        Json(serde_json::json!({
            "feature": "features",
            "service": "rust-web",
            "count": 20,
            "features": [
                "readyz","livez","startupz","healthz","version","features","status","peers","deps",
                "mesh-graph","chain-health","discover","capabilities","metrics-lite","config-public",
                "whoami","ping","ghas-proxy","routes","link-check"
            ],
            "ghas_origin": "kubernetes apiserver ready/live + GHAS dual-engine search mesh",
            "native": true
        }))
    }
    async fn mesh_readyz() -> impl IntoResponse {
        Json(
            serde_json::json!({"feature":"readyz","service":"rust-web","ready":true,"ghas":"k8s-readyz"}),
        )
    }
    async fn mesh_livez() -> impl IntoResponse {
        Json(serde_json::json!({"feature":"livez","service":"rust-web","live":true}))
    }
    async fn mesh_whoami() -> impl IntoResponse {
        Json(serde_json::json!({
            "feature":"whoami","service":"rust-web","role":"ops-dashboard",
            "ghas_borrow":"k8s-style /ops/api/* status surfaces"
        }))
    }
    async fn mesh_status() -> impl IntoResponse {
        Json(serde_json::json!({
            "feature":"status","service":"rust-web","role":"ops-dashboard","local_ok":true
        }))
    }
    async fn mesh_routes() -> impl IntoResponse {
        Json(serde_json::json!({
            "feature":"routes","service":"rust-web",
            "routes":["/mesh/features","/mesh/readyz","/mesh/livez","/mesh/whoami","/mesh/status","/mesh/routes"],
            "hub":"http://127.0.0.1:25115/mesh/s/rust-web/{feature}"
        }))
    }
    let app = Router::new()
        .route("/health", get(health))
        .route("/mesh", get(mesh_features))
        .route("/mesh/", get(mesh_features))
        .route("/mesh/features", get(mesh_features))
        .route("/mesh/readyz", get(mesh_readyz))
        .route("/mesh/livez", get(mesh_livez))
        .route("/mesh/whoami", get(mesh_whoami))
        .route("/mesh/status", get(mesh_status))
        .route("/mesh/routes", get(mesh_routes))
        // Chat UI is llama-swap :25100/ui — no proxy chat on this dashboard
        .route("/ops/api/logs", get(get_logs))
        .route("/ops/api/status", get(get_status))
        .route("/ops/api/telemetry", get(get_telemetry))
        .route("/ops/api/models", get(get_models_meta))
        .route("/ops/api/architecture", get(get_arch_live))
        .route("/ops/api/integrations", get(get_integrations))
        .route("/ops/api/fleet/last", get(get_fleet_last))
        .route("/ops/api/gpu/metrics", get(get_gpu_metrics))
        .route("/ops/api/squawk/channels", get(get_squawk_channels))
        .route("/ops/api/squawk/:channel", get(get_squawk_channel))
        .route(
            "/ops/api/mesh",
            get(|| async {
                // Proxy mesh-hub chain-health for dashboard JS (same-origin)
                let client = Client::builder()
                    .timeout(std::time::Duration::from_secs(4))
                    .build()
                    .unwrap_or_else(|_| Client::new());
                match client
                    .get("http://127.0.0.1:25115/mesh/chain-health")
                    .header("accept-encoding", "identity")
                    .send()
                    .await
                {
                    Ok(resp) => {
                        let status = resp.status();
                        let body = resp.text().await.unwrap_or_else(|_| "{}".into());
                        (
                            axum::http::StatusCode::from_u16(status.as_u16())
                                .unwrap_or(axum::http::StatusCode::BAD_GATEWAY),
                            [(axum::http::header::CONTENT_TYPE, "application/json")],
                            body,
                        )
                            .into_response()
                    }
                    Err(e) => (
                        axum::http::StatusCode::BAD_GATEWAY,
                        [(axum::http::header::CONTENT_TYPE, "application/json")],
                        format!(r#"{{"error":"mesh_hub_unreachable","detail":"{e}"}}"#),
                    )
                        .into_response(),
                }
            }),
        )
        .route("/api/agents/roster", get(agents::roster))
        .route("/api/agents/:name", get(agents::agent_history))
        .route("/ws/fleet", get(agents::ws_fleet))
        .route("/ops/api/mesh/features", get(proxy_mesh_features))
        // llama-swap API surface proxied for the built herd/mesh UIs
        // (the Svelte bundle fetches /v1, /api, /logs, /upstream, /unload, /sdapi).
        .route("/v1/*rest", any(proxy_llama_swap))
        .route("/api/*rest", any(proxy_llama_swap))
        .route("/logs/*rest", any(proxy_llama_swap))
        .route("/upstream/*rest", any(proxy_llama_swap))
        .route("/unload/*rest", any(proxy_llama_swap))
        .route("/sdapi/*rest", any(proxy_llama_swap))
        .nest_service("/herd-ui", herd_ui)
        .nest_service("/mesh-ui", mesh_ui)
        .nest_service("/", s);

    let p: u16 = std::env::var("RUST_WEB_PORT")
        .ok()
        .and_then(|x| x.parse().ok())
        .unwrap_or(25101);
    let a = SocketAddr::from(([0, 0, 0, 0], p));
    println!("rust web http://{}", a);
    let l = tokio::net::TcpListener::bind(a).await.unwrap();
    axum::serve(l, app).await.unwrap()
}

/// Reverse-proxy a request to the local llama-swap herd API (:25100).
/// Lets the built Svelte UIs (served at /herd-ui and /mesh-ui) call the
/// herd API through the same origin without a separate CORS surface.
async fn proxy_llama_swap(req: axum::http::Request<axum::body::Body>) -> impl IntoResponse {
    let (parts, body) = req.into_parts();
    let path = parts.uri.path().to_string();
    let query = parts
        .uri
        .query()
        .map(|q| format!("?{q}"))
        .unwrap_or_default();
    let url = format!("http://127.0.0.1:25100{path}{query}");
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .unwrap_or_else(|_| Client::new());
    let body_bytes = match axum::body::to_bytes(body, 16 * 1024 * 1024).await {
        Ok(b) => b,
        Err(_) => {
            return (
                axum::http::StatusCode::BAD_REQUEST,
                "request body too large",
            )
                .into_response()
        }
    };
    let mut rb = client
        .request(parts.method.clone(), &url)
        .body(body_bytes.to_vec());
    for (k, v) in parts.headers.iter() {
        if k == axum::http::header::HOST || k == axum::http::header::CONTENT_LENGTH {
            continue;
        }
        rb = rb.header(k, v);
    }
    match rb.send().await {
        Ok(resp) => {
            let status = axum::http::StatusCode::from_u16(resp.status().as_u16())
                .unwrap_or(axum::http::StatusCode::BAD_GATEWAY);
            let mut builder = axum::http::Response::builder().status(status);
            for (k, v) in resp.headers().iter() {
                if k == axum::http::header::TRANSFER_ENCODING
                    || k == axum::http::header::CONTENT_LENGTH
                {
                    continue;
                }
                builder = builder.header(k, v);
            }
            let bytes = resp.bytes().await.unwrap_or_default();
            match builder.body(axum::body::Body::from(bytes)) {
                Ok(r) => r.into_response(),
                Err(_) => (
                    axum::http::StatusCode::BAD_GATEWAY,
                    "proxy response build failed",
                )
                    .into_response(),
            }
        }
        Err(e) => (
            axum::http::StatusCode::BAD_GATEWAY,
            format!("llama-swap unreachable: {e}"),
        )
            .into_response(),
    }
}

/// Simple GET proxy for a fixed upstream URL (mesh-hub JSON).
async fn proxy_simple(url: &str) -> impl IntoResponse {
    match Client::new()
        .get(url)
        .timeout(Duration::from_secs(10))
        .send()
        .await
    {
        Ok(resp) => {
            let status = axum::http::StatusCode::from_u16(resp.status().as_u16())
                .unwrap_or(axum::http::StatusCode::BAD_GATEWAY);
            let bytes = resp.bytes().await.unwrap_or_default();
            (status, bytes).into_response()
        }
        Err(e) => (
            axum::http::StatusCode::BAD_GATEWAY,
            format!("upstream unreachable: {e}"),
        )
            .into_response(),
    }
}

async fn proxy_mesh_features() -> impl IntoResponse {
    proxy_simple("http://127.0.0.1:25115/mesh/features").await
}
