//! HTTP API. Every route requires the bearer token; secret values are
//! returned only to authenticated callers and are never logged.

use axum::{
    extract::{Path, State},
    http::{header, Request, StatusCode},
    middleware::{self, Next},
    response::{IntoResponse, Json, Response},
    routing::{get, post, put},
    Router,
};
use serde::{Deserialize, Serialize};
use subtle::ConstantTimeEq;
use zeroize::Zeroizing;

use crate::{store::SecretMeta, AppState};

#[derive(Deserialize)]
struct PutBody {
    value: String,
    purpose: Option<String>,
}

#[derive(Deserialize)]
struct RotateBody {
    value: String,
}

#[derive(Serialize)]
struct ValueBody {
    value: String,
}

#[derive(Serialize)]
struct ErrorBody {
    error: String,
}

fn err(status: StatusCode, msg: &str) -> Response {
    (status, Json(ErrorBody { error: msg.to_string() })).into_response()
}

/// Bearer-token auth. Constant-time compare; rejects missing/mismatched tokens.
async fn auth_middleware(state: State<AppState>, req: Request<axum::body::Body>, next: Next) -> Response {
    let ok = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .and_then(|s| s.strip_prefix("Bearer "))
        .map(|tok| {
            tok.as_bytes().ct_eq(state.api_token.as_bytes()).into()
        })
        .unwrap_or(false);
    if !ok {
        return err(StatusCode::UNAUTHORIZED, "unauthorized");
    }
    next.run(req).await
}

async fn health() -> &'static str {
    "ok"
}

async fn put_secret(
    State(state): State<AppState>,
    Path(name): Path<String>,
    Json(body): Json<PutBody>,
) -> Response {
    if name.is_empty() || name.len() > 128 {
        return err(StatusCode::BAD_REQUEST, "bad secret name");
    }
    match state
        .store
        .put(&name, body.purpose.as_deref(), Zeroizing::new(body.value))
    {
        Ok(meta) => (StatusCode::OK, Json(meta)).into_response(),
        Err(e) => {
            tracing::error!(secret = %name, "put failed: {e:#}");
            err(StatusCode::INTERNAL_SERVER_ERROR, "store failed")
        }
    }
}

async fn get_secret(State(state): State<AppState>, Path(name): Path<String>) -> Response {
    match state.store.get_value(&name) {
        Ok(Some(v)) => Json(ValueBody { value: v.to_string() }).into_response(),
        Ok(None) => err(StatusCode::NOT_FOUND, "no such secret"),
        Err(e) => {
            tracing::error!(secret = %name, "get failed: {e:#}");
            err(StatusCode::INTERNAL_SERVER_ERROR, "store failed")
        }
    }
}

async fn list_secrets(State(state): State<AppState>) -> Response {
    match state.store.list_meta() {
        Ok(items) => Json(items).into_response(),
        Err(e) => {
            tracing::error!("list failed: {e:#}");
            err(StatusCode::INTERNAL_SERVER_ERROR, "store failed")
        }
    }
}

async fn rotate_secret(
    State(state): State<AppState>,
    Path(name): Path<String>,
    Json(body): Json<RotateBody>,
) -> Response {
    match state.store.rotate(&name, Zeroizing::new(body.value)) {
        Ok(Some(meta)) => (StatusCode::OK, Json(meta)).into_response(),
        Ok(None) => err(StatusCode::NOT_FOUND, "no such secret"),
        Err(e) => {
            tracing::error!(secret = %name, "rotate failed: {e:#}");
            err(StatusCode::INTERNAL_SERVER_ERROR, "store failed")
        }
    }
}

pub fn router(state: AppState) -> Router {
    let authed = Router::new()
        .route("/secrets", get(list_secrets))
        .route("/secrets/{name}", put(put_secret).get(get_secret))
        .route("/secrets/{name}/rotate", post(rotate_secret))
        .route_layer(middleware::from_fn_with_state(state.clone(), auth_middleware));
    Router::new()
        .route("/health", get(health))
        .merge(authed)
        .with_state(state)
}

// Re-export for tests/hardening later.
#[allow(dead_code)]
fn _meta_shape(_: &SecretMeta) {}
