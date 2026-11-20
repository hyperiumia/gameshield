mod auth;
mod handlers;
mod models;

use axum::{
    routing::{get, post},
    Router,
};
use sqlx::postgres::PgPoolOptions;
use std::{env, sync::Arc};
use tracing_subscriber::EnvFilter;

pub struct AppState {
    pub pool: sqlx::PgPool,
    pub api_key: String,
    pub secret: String,
    pub replay_secs: i64,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse().unwrap()))
        .init();

    let database_url = env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://gameshield:gameshield@localhost:5432/gameshield".into());
    let api_key = env::var("GAMESHIELD_API_KEY").unwrap_or_else(|_| "dev-key".into());
    let secret = env::var("GAMESHIELD_HMAC_SECRET").unwrap_or_else(|_| "dev-secret".into());
    let replay_secs: i64 = env::var("GAMESHIELD_REPLAY_SECS")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(300);

    if api_key == "dev-key" {
        tracing::warn!(
            "using DEV credentials — set GAMESHIELD_API_KEY / GAMESHIELD_HMAC_SECRET in production"
        );
    }

    let pool = connect_with_retry(&database_url).await;
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .expect("migrations failed");

    let state = Arc::new(AppState {
        pool,
        api_key,
        secret,
        replay_secs,
    });

    let app = Router::new()
        .route("/healthz", get(handlers::healthz))
        .route("/v1/events", post(handlers::ingest))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080")
        .await
        .expect("failed to bind :8080");
    tracing::info!("gameshield-ingest listening on :8080");
    axum::serve(listener, app).await.expect("server error");
}

async fn connect_with_retry(url: &str) -> sqlx::PgPool {
    for attempt in 1..=30 {
        match PgPoolOptions::new().max_connections(5).connect(url).await {
            Ok(pool) => return pool,
            Err(e) => {
                tracing::warn!("postgres not ready (attempt {attempt}/30): {e}");
                tokio::time::sleep(std::time::Duration::from_secs(2)).await;
            }
        }
    }
    panic!("could not connect to postgres at {url}");
}
