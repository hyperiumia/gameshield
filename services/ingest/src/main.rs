use axum::{routing::get, Json, Router};
use serde_json::json;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let app = Router::new().route("/healthz", get(healthz));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080")
        .await
        .expect("failed to bind :8080");

    tracing::info!("gameshield-ingest listening on :8080");
    axum::serve(listener, app).await.expect("server error");
}

async fn healthz() -> Json<serde_json::Value> {
    Json(json!({ "status": "ok", "service": "gameshield-ingest", "version": "0.1.0" }))
}
