use axum::{routing::{get, post}, Router, Json};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

#[derive(Serialize)] struct HealthResponse { status: String }
#[derive(Deserialize)] struct ChatRequest { prompt: String }
#[derive(Serialize)] struct ChatResponse { response: String }

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse { status: "ok".to_string() })
}

async fn chat(Json(req): Json<ChatRequest>) -> Json<ChatResponse> {
    Json(ChatResponse { response: format!("Echo: {}", req.prompt) })
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health))
        .route("/chat", post(chat))
        .fallback(axum::routing::get(|| async { "Sovereign Rust API" }));
    let addr = SocketAddr::from(([0, 0, 0, 0], 25010));
    println!("Rust algo web on http://{}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
