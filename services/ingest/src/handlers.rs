use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    Json,
};
use serde_json::{json, Value};
use std::sync::Arc;

use crate::models::{insert, BatchPayload, EconomicEvent};
use crate::{auth, AppState};

pub async fn healthz() -> Json<Value> {
    Json(json!({ "status": "ok", "service": "gameshield-ingest", "version": "0.2.0" }))
}

fn header<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    headers.get(name).and_then(|v| v.to_str().ok())
}

pub async fn ingest(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    body: String,
) -> impl IntoResponse {
    let (Some(key), Some(ts), Some(sig)) = (
        header(&headers, "x-gs-key"),
        header(&headers, "x-gs-timestamp"),
        header(&headers, "x-gs-signature"),
    ) else {
        return (
            StatusCode::UNAUTHORIZED,
            Json(json!({ "error": "missing auth headers (x-gs-key, x-gs-timestamp, x-gs-signature)" })),
        );
    };

    if let Err(reason) = auth::verify(
        &state.secret,
        key,
        &state.api_key,
        ts,
        &body,
        sig,
        state.replay_secs,
    ) {
        return (StatusCode::UNAUTHORIZED, Json(json!({ "error": reason })));
    }

    let batch: BatchPayload = match serde_json::from_str(&body) {
        Ok(b) => b,
        Err(e) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(json!({ "error": format!("invalid batch: {e}") })),
            )
        }
    };

    let mut accepted = 0u32;
    let mut stored: Vec<Value> = Vec::new();
    let mut rejected: Vec<Value> = Vec::new();

    for raw in &batch.events {
        let raw_id = raw.get("event_id").cloned().unwrap_or(Value::Null);
        match serde_json::from_value::<EconomicEvent>(raw.clone()) {
            Err(e) => rejected.push(json!({ "event_id": raw_id, "reason": format!("schema: {e}") })),
            Ok(ev) => match ev.validate() {
                Err(reason) => rejected.push(json!({ "event_id": raw_id, "reason": reason })),
                Ok(()) => match insert(&state.pool, &ev).await {
                    Err(e) => {
                        rejected.push(json!({ "event_id": raw_id, "reason": format!("db: {e}") }))
                    }
                    Ok(()) => {
                        accepted += 1;
                        stored.push(json!(ev.event_id));
                    }
                },
            },
        }
    }

    (
        StatusCode::OK,
        Json(json!({ "accepted": accepted, "rejected": rejected, "stored": stored })),
    )
}
