// src/main.rs
mod algo;
mod llm;

use axum::{
    routing::{get, post},
    Router, Json,
};
use serde::{Serialize, Deserialize};
use std::net::SocketAddr;
use tower_http::services::ServeDir;
use algo::{Weights, ToolScore};
use llm::{AdvisorRequest, AdvisorResponse, consult_advisor};

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    model: Option<String>,
}

#[derive(Deserialize)]
struct RankRequest {
    nix_overhead: f32,
    tui_gui_polish: f32,
    performance: f32,
    setup_speed: f32,
    orchestration: f32,
    portability: f32,
}

async fn health() -> Json<HealthResponse> {
    let model = std::env::var("LLM_PROXY_URL").ok().map(|url| format!("via {}", url));
    Json(HealthResponse {
        status: "ok".to_string(),
        model,
    })
}

async fn rank(Json(req): Json<RankRequest>) -> Json<Vec<ToolScore>> {
    let weights = Weights {
        nix_overhead: req.nix_overhead,
        tui_gui_polish: req.tui_gui_polish,
        performance: req.performance,
        setup_speed: req.setup_speed,
        orchestration: req.orchestration,
        portability: req.portability,
    };
    Json(algo::rank_tools(weights))
}

async fn advisor(Json(req): Json<AdvisorRequest>) -> Json<AdvisorResponse> {
    match consult_advisor(req).await {
        Ok(res) => Json(res),
        Err(e) => Json(AdvisorResponse {
            weights: Weights {
                nix_overhead: 0.0,
                tui_gui_polish: 0.0,
                performance: 0.0,
                setup_speed: 0.0,
                orchestration: 0.0,
                portability: 0.0,
            },
            explanation: format!("Advisor failed: {}", e),
        }),
    }
}

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();

    let static_service = ServeDir::new("static");

    let app = Router::new()
        .route("/health", get(health))
        .route("/api/rank", post(rank))
        .route("/api/ai/advisor", post(advisor))
        .nest_service("/", static_service);

    let port: u16 = std::env::var("RUST_WEB_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(25010);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Sovereign DevOps Advisor on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
