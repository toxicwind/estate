mod fleet;
mod gpu;
mod watchdog;

use axum::{response::IntoResponse, routing::get, Json, Router};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::net::SocketAddr;
use tower_http::services::ServeDir;

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

#[derive(Serialize)]
struct ServiceInfo {
    name: String,
    port: u16,
    url: String,
    category: String,
    kind: String,
    online: bool,
    latency_ms: u128,
}

#[derive(Serialize)]
struct AllServicesResponse {
    services: Vec<ServiceInfo>,
    online_count: usize,
    total_count: usize,
}

async fn get_all_services() -> Json<AllServicesResponse> {
    let services = vec![
        (
            "LLaMA Swap",
            25100,
            "http://localhost:25100",
            "LLM",
            "LLM Proxy",
        ),
        (
            "Rust Web",
            25101,
            "http://localhost:25101",
            "Core",
            "Dashboard",
        ),
        ("Yote", 25102, "http://localhost:25102", "Core", "Service"),
        (
            "OpenFang",
            25103,
            "http://localhost:25103",
            "Core",
            "Service",
        ),
        (
            "Sovereign Router",
            25104,
            "http://localhost:25104/health",
            "Core",
            "Router",
        ),
        (
            "Prometheus",
            25105,
            "http://localhost:25105",
            "Monitoring",
            "Metrics",
        ),
        (
            "HF Downloader",
            25106,
            "http://localhost:25106",
            "LLM",
            "Model Downloader",
        ),
        (
            "Null-G Proxy",
            25107,
            "http://localhost:25107",
            "Core",
            "Search",
        ),
        (
            "MCP Proxy",
            25109,
            "http://localhost:25109",
            "MCP",
            "Gateway",
        ),
        (
            "Grafana",
            25110,
            "http://localhost:25110",
            "Monitoring",
            "Dashboards",
        ),
        (
            "GHAS API",
            25112,
            "http://localhost:25112",
            "MCP",
            "GitHub Search",
        ),
        (
            "GHAS MCP",
            25113,
            "http://localhost:25113",
            "MCP",
            "MCP Server",
        ),
        ("Mesh Hub", 25115, "http://localhost:25115", "Mesh", "Mesh"),
        (
            "MCP Gateway",
            25120,
            "http://localhost:25120",
            "MCP",
            "Gateway",
        ),
        (
            "Byte Vision",
            25121,
            "http://localhost:25121",
            "MCP",
            "Vision MCP",
        ),
        (
            "Byte Vision Proxy",
            25122,
            "http://localhost:25122",
            "MCP",
            "Proxy",
        ),
        (
            "Qdrant",
            6333,
            "http://localhost:6333/dashboard",
            "Data",
            "Vector DB",
        ),
        ("Redis Sovereign", 25199, "", "Data", "Cache"),
        ("Redis Telemetry", 25198, "", "Data", "Telemetry"),
        (
            "Browserless",
            25130,
            "http://localhost:25130",
            "MCP",
            "Browser",
        ),
        (
            "Itvx-Morphe",
            25140,
            "http://localhost:25140",
            "Core",
            "Engine",
        ),
    ];

    let mut results = Vec::new();
    for (name, port, url, category, kind) in services {
        let start = std::time::Instant::now();
        let online = tokio::net::TcpStream::connect(format!("127.0.0.1:{}", port))
            .await
            .is_ok();
        let latency_ms = start.elapsed().as_millis();
        results.push(ServiceInfo {
            name: name.into(),
            port,
            url: url.into(),
            category: category.into(),
            kind: kind.into(),
            online,
            latency_ms,
        });
    }

    let online_count = results.iter().filter(|s| s.online).count();
    let total_count = results.len();

    Json(AllServicesResponse {
        services: results,
        online_count,
        total_count,
    })
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
        .route("/ops/api/services/all", get(get_all_services))
        .route("/ops/api/integrations", get(get_integrations))
        .route("/ops/api/fleet/last", get(get_fleet_last))
        .route("/ops/api/gpu/metrics", get(get_gpu_metrics))
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
