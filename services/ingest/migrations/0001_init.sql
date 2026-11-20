CREATE TABLE IF NOT EXISTS economic_events (
    id               BIGSERIAL PRIMARY KEY,
    event_id         UUID NOT NULL UNIQUE,
    server_id        TEXT NOT NULL,
    occurred_at      TIMESTAMPTZ NOT NULL,
    type             TEXT NOT NULL,
    actor_player_id  TEXT NOT NULL,
    actor_name       TEXT,
    actor_role       TEXT NOT NULL DEFAULT 'player',
    currency         TEXT,
    amount           DOUBLE PRECISION,
    balance_after    DOUBLE PRECISION,
    subject_kind     TEXT,
    subject_sku      TEXT,
    subject_quantity DOUBLE PRECISION,
    source_resource  TEXT NOT NULL,
    source_event     TEXT,
    counterparty     TEXT,
    payload          JSONB NOT NULL,
    received_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_server_time ON economic_events (server_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_actor ON economic_events (server_id, actor_player_id);
