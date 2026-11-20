use hmac::{Hmac, Mac};
use sha2::Sha256;

/// Verifies a signed batch: HMAC-SHA256(secret, "{timestamp}.{body}") as hex,
/// plus api-key match and a replay window on the timestamp.
pub fn verify(
    secret: &str,
    key: &str,
    api_key: &str,
    timestamp: &str,
    body: &str,
    signature: &str,
    replay_secs: i64,
) -> Result<(), String> {
    if key != api_key {
        return Err("bad api key".into());
    }
    let ts: i64 = timestamp
        .parse()
        .map_err(|_| "timestamp must be unix seconds".to_string())?;
    let now = chrono::Utc::now().timestamp();
    if (now - ts).abs() > replay_secs {
        return Err("stale timestamp outside replay window".into());
    }
    let mut mac = Hmac::<Sha256>::new_from_slice(secret.as_bytes()).expect("hmac key length ok");
    mac.update(format!("{timestamp}.{body}").as_bytes());
    let sig = hex::decode(signature.trim()).map_err(|_| "signature is not hex".to_string())?;
    mac.verify_slice(&sig).map_err(|_| "signature mismatch".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sign(secret: &str, ts: &str, body: &str) -> String {
        let mut mac = Hmac::<Sha256>::new_from_slice(secret.as_bytes()).unwrap();
        mac.update(format!("{ts}.{body}").as_bytes());
        hex::encode(mac.finalize().into_bytes())
    }

    #[test]
    fn accepts_valid_signature() {
        let ts = chrono::Utc::now().timestamp().to_string();
        let body = r#"{"events":[]}"#;
        let sig = sign("s3cret", &ts, body);
        assert!(verify("s3cret", "k", "k", &ts, body, &sig, 300).is_ok());
    }

    #[test]
    fn rejects_wrong_signature() {
        let ts = chrono::Utc::now().timestamp().to_string();
        assert!(verify("s3cret", "k", "k", &ts, "{}", "deadbeef", 300).is_err());
    }

    #[test]
    fn rejects_wrong_key() {
        let ts = chrono::Utc::now().timestamp().to_string();
        let sig = sign("s3cret", &ts, "{}");
        assert!(verify("s3cret", "other", "k", &ts, "{}", &sig, 300).is_err());
    }

    #[test]
    fn rejects_stale_timestamp() {
        let ts = (chrono::Utc::now().timestamp() - 10_000).to_string();
        let sig = sign("s3cret", &ts, "{}");
        assert!(verify("s3cret", "k", "k", &ts, "{}", &sig, 300).is_err());
    }
}
