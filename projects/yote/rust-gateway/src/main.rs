// Yote — Unified Messaging Gateway
// Telegram + Discord → LLM (llama-swap :25100)

mod telegram;
mod discord;

use std::env;
use tracing::{info, error};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let port = env::var("YOTE_PORT").unwrap_or_else(|_| "25102".to_string());
    info!("Yote gateway starting on port {}", port);

    // TODO: Initialize Telegram bot
    // TODO: Initialize Discord gateway
    // TODO: Connect to llama-swap on :25100

    info!("Yote ready. Telegram + Discord unified.");

    // Keep alive
    tokio::signal::ctrl_c().await.ok();
    info!("Yote shutting down.");
}
