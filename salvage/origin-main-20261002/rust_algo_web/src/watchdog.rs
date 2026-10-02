use axum::{routing::get, Json, Router};
use serde_json::json;
use std::net::SocketAddr;

pub async fn run(port: u16) {
    let app = Router::new()
        .route("/health", get(|| async { "ok" }))
        .fallback(move || async move {
            Json(json!({
                "svc": "watchdog",
                "port": port
            }))
        });

    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    println!("Watchdog running on http://{}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
