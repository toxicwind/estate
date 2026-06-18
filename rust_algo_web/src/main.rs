mod algo;
mod llm;

use axum::{
    routing::post,
    Json, Router,
    response::IntoResponse,
    http::StatusCode,
};
use tower_http::{
    services::ServeDir,
    cors::CorsLayer,
};
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    let cors = CorsLayer::permissive();

    // Serve static files from "static" directory, fallback to index.html
    let serve_dir = ServeDir::new("static")
        .append_index_html_on_directories(true);

    let app = Router::new()
        .route("/api/rank", post(handle_rank))
        .route("/api/ai/advisor", post(handle_advisor))
        .fallback_service(serve_dir)
        .layer(cors);

    let addr = SocketAddr::from(([0, 0, 0, 0], 25010));
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║      DEV ENV & PROCESS MANAGER RANKER BACKEND (RUST)       ║");
    println!("║      Listening on: http://localhost:25010                  ║");
    println!("╚════════════════════════════════════════════════════════════╝");

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn handle_rank(
    Json(req): Json<algo::Weights>
) -> impl IntoResponse {
    let ranked = algo::rank_tools(req);
    (StatusCode::OK, Json(ranked))
}

async fn handle_advisor(
    Json(req): Json<llm::AdvisorRequest>
) -> impl IntoResponse {
    match llm::consult_advisor(req).await {
        Ok(advice) => (StatusCode::OK, Json(serde_json::json!({ "success": true, "data": advice }))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({ "success": false, "error": e }))
        ),
    }
}
