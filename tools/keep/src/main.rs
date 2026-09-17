//! keep — the single home for secrets.
//!
//! age-encrypted secret store backed by SQLite. Secret plaintext is held in
//! `Zeroizing` wrappers only, and is never written to logs or disk in the clear.

pub mod api;
pub mod crypto;
pub mod store;

use std::{net::SocketAddr, sync::Arc};

use tracing::{info, warn};

#[derive(Clone)]
pub struct AppState {
    pub store: Arc<store::SecretStore>,
    pub api_token: zeroize::Zeroizing<String>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let db_path =
        std::env::var("KEEP_DB_PATH").unwrap_or_else(|_| "keep.db".to_string());
    let api_token = std::env::var("KEEP_API_TOKEN").map_err(|_| {
        anyhow::anyhow!("KEEP_API_TOKEN must be set (bearer token for all API calls)")
    })?;
    if api_token.len() < 32 {
        anyhow::bail!("KEEP_API_TOKEN must be at least 32 characters");
    }

    let identity = crypto::load_identity()?;
    let store = Arc::new(store::SecretStore::open(&db_path, identity)?);

    let state = AppState {
        store,
        api_token: zeroize::Zeroizing::new(api_token),
    };

    let app = api::router(state);

    let addr: SocketAddr = std::env::var("KEEP_BIND")
        .unwrap_or_else(|_| "127.0.0.1:25900".to_string())
        .parse()
        .map_err(|e| anyhow::anyhow!("bad KEEP_BIND: {e}"))?;

    match (
        std::env::var("KEEP_TLS_CERT").ok(),
        std::env::var("KEEP_TLS_KEY").ok(),
    ) {
        (Some(cert), Some(key)) => {
            info!(%addr, "keep listening with TLS (rustls)");
            let config =
                axum_server::tls_rustls::RustlsConfig::from_pem_file(cert, key).await?;
            axum_server::bind_rustls(addr, config)
                .serve(app.into_make_service())
                .await?;
        }
        _ => {
            warn!(%addr, "keep listening WITHOUT TLS (set KEEP_TLS_CERT/KEEP_TLS_KEY to enable)");
            let listener = tokio::net::TcpListener::bind(addr).await?;
            axum::serve(listener, app).await?;
        }
    }
    Ok(())
}
