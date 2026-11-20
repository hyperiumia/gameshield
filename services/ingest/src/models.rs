use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use uuid::Uuid;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum EventType {
    #[serde(rename = "money.credit")] MoneyCredit,
    #[serde(rename = "money.debit")] MoneyDebit,
    #[serde(rename = "money.transfer")] MoneyTransfer,
    #[serde(rename = "item.grant")] ItemGrant,
    #[serde(rename = "item.remove")] ItemRemove,
    #[serde(rename = "item.transfer")] ItemTransfer,
    #[serde(rename = "vehicle.grant")] VehicleGrant,
    #[serde(rename = "vehicle.remove")] VehicleRemove,
    #[serde(rename = "property.transfer")] PropertyTransfer,
    #[serde(rename = "purchase")] Purchase,
    #[serde(rename = "sale")] Sale,
    #[serde(rename = "trade")] Trade,
    #[serde(rename = "admin.override")] AdminOverride,
}

impl EventType {
    pub fn as_str(&self) -> &'static str {
        match self {
            EventType::MoneyCredit => "money.credit",
            EventType::MoneyDebit => "money.debit",
            EventType::MoneyTransfer => "money.transfer",
            EventType::ItemGrant => "item.grant",
            EventType::ItemRemove => "item.remove",
            EventType::ItemTransfer => "item.transfer",
            EventType::VehicleGrant => "vehicle.grant",
            EventType::VehicleRemove => "vehicle.remove",
            EventType::PropertyTransfer => "property.transfer",
            EventType::Purchase => "purchase",
            EventType::Sale => "sale",
            EventType::Trade => "trade",
            EventType::AdminOverride => "admin.override",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum ActorRole {
    #[default]
    #[serde(rename = "player")] Player,
    #[serde(rename = "staff")] Staff,
    #[serde(rename = "system")] System,
}

impl ActorRole {
    pub fn as_str(&self) -> &'static str {
        match self {
            ActorRole::Player => "player",
            ActorRole::Staff => "staff",
            ActorRole::System => "system",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Actor {
    pub player_id: String,
    pub display_name: Option<String>,
    #[serde(default)]
    pub role: ActorRole,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Economy {
    pub currency: Option<String>,
    pub amount: Option<f64>,
    pub balance_after: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subject {
    pub kind: Option<String>,
    pub sku: Option<String>,
    pub quantity: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Source {
    pub resource: String,
    pub event_name: Option<String>,
    pub counterparty_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomicEvent {
    pub schema_version: String,
    pub event_id: Uuid,
    pub server_id: String,
    pub occurred_at: DateTime<Utc>,
    #[serde(rename = "type")]
    pub event_type: EventType,
    pub actor: Actor,
    pub economy: Option<Economy>,
    pub subject: Option<Subject>,
    pub source: Source,
    pub context: Option<Value>,
}

impl EconomicEvent {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema_version != "1" {
            return Err(format!("schema_version must be '1', got '{}'", self.schema_version));
        }
        if self.server_id.is_empty() || self.server_id.len() > 64 {
            return Err("server_id must be 1..=64 chars".into());
        }
        if self.actor.player_id.is_empty() || self.actor.player_id.len() > 128 {
            return Err("actor.player_id must be 1..=128 chars".into());
        }
        if self.source.resource.is_empty() || self.source.resource.len() > 128 {
            return Err("source.resource must be 1..=128 chars".into());
        }
        if let Some(sku) = &self.subject.as_ref().and_then(|s| s.sku.as_ref()) {
            if sku.len() > 128 {
                return Err("subject.sku must be <= 128 chars".into());
            }
        }
        if let Some(e) = &self.economy {
            for (name, v) in [("amount", e.amount), ("balance_after", e.balance_after)] {
                if let Some(v) = v {
                    if !v.is_finite() {
                        return Err(format!("economy.{name} must be finite"));
                    }
                }
            }
        }
        Ok(())
    }
}

#[derive(Debug, Deserialize)]
pub struct BatchPayload {
    pub sent_at: Option<String>,
    pub events: Vec<Value>,
}

pub async fn insert(pool: &sqlx::PgPool, ev: &EconomicEvent) -> Result<(), sqlx::Error> {
    let payload = serde_json::to_value(ev).unwrap_or(Value::Null);
    let (currency, amount, balance_after) = match &ev.economy {
        Some(e) => (e.currency.clone(), e.amount, e.balance_after),
        None => (None, None, None),
    };
    let (subject_kind, subject_sku, subject_quantity) = match &ev.subject {
        Some(s) => (s.kind.clone(), s.sku.clone(), s.quantity),
        None => (None, None, None),
    };

    sqlx::query(
        "INSERT INTO economic_events
           (event_id, server_id, occurred_at, type, actor_player_id, actor_name, actor_role,
            currency, amount, balance_after, subject_kind, subject_sku, subject_quantity,
            source_resource, source_event, counterparty, payload)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
         ON CONFLICT (event_id) DO NOTHING",
    )
    .bind(ev.event_id)
    .bind(&ev.server_id)
    .bind(ev.occurred_at)
    .bind(ev.event_type.as_str())
    .bind(&ev.actor.player_id)
    .bind(&ev.actor.display_name)
    .bind(ev.actor.role.as_str())
    .bind(currency)
    .bind(amount)
    .bind(balance_after)
    .bind(subject_kind)
    .bind(subject_sku)
    .bind(subject_quantity)
    .bind(&ev.source.resource)
    .bind(&ev.source.event_name)
    .bind(&ev.source.counterparty_id)
    .bind(payload)
    .execute(pool)
    .await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_json() -> String {
        r#"{
            "schema_version": "1",
            "event_id": "11111111-1111-4111-8111-111111111101",
            "server_id": "srv-demo",
            "occurred_at": "2026-11-20T10:00:00Z",
            "type": "money.credit",
            "actor": { "player_id": "p-042", "display_name": "Demo", "role": "player" },
            "economy": { "currency": "USD", "amount": 250000.0 },
            "source": { "resource": "qb-core", "event_name": "paid" }
        }"#
        .to_string()
    }

    #[test]
    fn parses_valid_event() {
        let ev: EconomicEvent = serde_json::from_str(&valid_json()).unwrap();
        assert_eq!(ev.event_type.as_str(), "money.credit");
        assert!(ev.validate().is_ok());
    }

    #[test]
    fn rejects_missing_type() {
        let bad = valid_json().replace(r#""type": "money.credit","#, "");
        assert!(serde_json::from_str::<EconomicEvent>(&bad).is_err());
    }

    #[test]
    fn rejects_bad_schema_version() {
        let mut ev: EconomicEvent = serde_json::from_str(&valid_json()).unwrap();
        ev.schema_version = "9".into();
        assert!(ev.validate().is_err());
    }
}
