use axum::{
    body::Body,
    extract::{State, Json},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Router,
};
use futures::StreamExt;
use serde::{Deserialize, Serialize};
use std::{sync::Arc, time::Duration};
use tokio::sync::RwLock;

#[derive(Clone)]
struct AppState {
    llama_url: String,
    client: reqwest::Client,
    model_name: String,
}

#[tokio::main]
async fn main() {
    let state = Arc::new(AppState {
        llama_url: std::env::var("LLAMA_URL").unwrap_or("http://localhost:8080".to_string()),
        client: reqwest::Client::builder().timeout(Duration::from_secs(300)).build().unwrap(),
        model_name: std::env::var("MODEL_NAME").unwrap_or("sovereign-llama:latest".to_string()),
    });

    let app = Router::new()
        .route("/api/version", get(version))
        .route("/api/tags", get(tags))
        .route("/api/show", get(show))
        .route("/v1/models", get(v1_models))
        .route("/api/chat", post(proxy_chat_ollama))
        .route("/v1/chat/completions", post(proxy_chat_openai))
        .route("/api/generate", post(proxy_generate))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:11434").await.unwrap();
    println!("Ollama->Beellama Rust proxy on :11434 -> {}", std::env::var("LLAMA_URL").unwrap_or("http://localhost:8080".to_string()));
    axum::serve(listener, app).await.unwrap();
}

async fn version() -> Json<serde_json::Value> {
    Json(serde_json::json!({"version":"0.5.7"}))
}

async fn tags(State(s): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let models = fetch_models(&s).await;
    Json(serde_json::json!({"models": models}))
}

async fn show(State(s): State<Arc<AppState>>) -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "modelfile": format!("FROM {}", s.model_name),
        "details": {
            "family": "llama",
            "parameter_size": "9B",
            "quantization_level": "Q4_K_M"
        },
        "model_info": {
            "general.architecture": "qwen3_moe",
        },
        "capabilities": ["completion","chat"]
    }))
}

async fn v1_models(State(s): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let models = fetch_models(&s).await;
    let data: Vec<_> = models.iter().map(|m| serde_json::json!({
        "id": m["name"],
        "object": "model"
    })).collect();
    Json(serde_json::json!({"object":"list","data":data}))
}

async fn fetch_models(s: &AppState) -> Vec<serde_json::Value> {
    let url = format!("{}/v1/models", s.llama_url);
    if let Ok(resp) = s.client.get(&url).send().await {
        if let Ok(v) = resp.json::<serde_json::Value>().await {
            if let Some(arr) = v.get("data").and_then(|d| d.as_array()) {
                return arr.iter().map(|m| {
                    serde_json::json!({
                        "name": m.get("id").unwrap_or(&serde_json::Value::String(s.model_name.clone())),
                        "model": m.get("id").unwrap_or(&serde_json::Value::String(s.model_name.clone())),
                    })
                }).collect();
            }
        }
    }
    vec![serde_json::json!({"name": s.model_name, "model": s.model_name})]
}

#[derive(Deserialize)]
struct OllamaChat { model: String, messages: serde_json::Value, stream: Option<bool>, options: Option<serde_json::Value> }

async fn proxy_chat_ollama(State(s): State<Arc<AppState>>, Json(payload): Json<OllamaChat>) -> Response {
    let body = serde_json::json!({
        "model": payload.model,
        "messages": payload.messages,
        "stream": payload.stream.unwrap_or(true),
        "temperature": payload.options.as_ref().and_then(|o| o.get("temperature")),
    });
    proxy_stream(s, body).await
}

async fn proxy_chat_openai(State(s): State<Arc<AppState>>, Json(payload): Json<serde_json::Value>) -> Response {
    proxy_stream(s, payload).await
}

async fn proxy_generate(State(s): State<Arc<AppState>>, Json(payload): Json<serde_json::Value>) -> Response {
    let body = serde_json::json!({
        "model": payload.get("model").unwrap_or(&serde_json::Value::String(s.model_name.clone())),
        "prompt": payload.get("prompt").unwrap_or(&serde_json::Value::String("".to_string())),
        "stream": payload.get("stream").unwrap_or(&serde_json::Value::Bool(false)),
    });
    proxy_stream(s, body).await
}

async fn proxy_stream(s: Arc<AppState>, body: serde_json::Value) -> Response {
    let url = format!("{}/v1/chat/completions", s.llama_url);
    match s.client.post(&url).json(&body).send().await {
        Ok(resp) => {
            let status = resp.status();
            let stream = resp.bytes_stream();
            let body = Body::from_stream(stream);
            Response::builder().status(status).header("content-type","text/event-stream").body(body).unwrap()
        },
        Err(e) => (StatusCode::BAD_GATEWAY, e.to_string()).into_response(),
    }
}
