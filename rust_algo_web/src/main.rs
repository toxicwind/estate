mod watchdog;

use axum::{routing::get, Router, Json};
use serde::{Serialize, Deserialize};
use std::net::SocketAddr;
use tower_http::services::ServeDir;
use reqwest::Client;
use std::collections::HashMap;

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
    // Prefer explicit swap port. Never treat Caddy edge :25000 as llama-swap.
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
    let m = std::env::var("LLM_PROXY_URL").ok().map(|u| format!("via {}", u));
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
    let pc_res = cl.get("http://127.0.0.1:8080/processes").send().await;

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
            ("Caddy Edge", "caddy", 25000u16),
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
            map.insert(
                ui_name.to_string(),
                StatusResponse { online, port },
            );
        }
    } else {
        for (name, is_running) in pc_running {
            let ui_name = match name.as_str() {
                "caddy" => "Caddy Edge",
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
                "caddy" => 25000,
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
    let watchdog_online = cl.get(format!("http://127.0.0.1:{}/health", watchdog_port))
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
    if let Ok(content) = std::fs::read_to_string("/home/toxic/sovereign/tools/llama-swap/config.yaml") {
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
                    let val_str = trimmed[pos+1..].trim();
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
    let app = Router::new()
        .route("/health", get(health))
        // Chat UI is llama-swap :25100/ui — no proxy chat on this dashboard
        .route("/landing/api/logs", get(get_logs))
        .route("/landing/api/status", get(get_status))
        .route("/landing/api/telemetry", get(get_telemetry))
        .route("/landing/api/models", get(get_models_meta))
        .route("/landing/api/architecture", get(get_arch_live))
        .route("/landing/api/integrations", get(get_integrations))
        .route("/landing/api/fleet/last", get(get_fleet_last))
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
