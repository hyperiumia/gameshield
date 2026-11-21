export interface Actor {
  player_id: string;
  display_name?: string | null;
  role?: string;
}

export interface Economy {
  currency?: string | null;
  amount?: number | null;
  balance_after?: number | null;
}

export interface Subject {
  kind?: string | null;
  sku?: string | null;
  quantity?: number | null;
}

export interface Source {
  resource: string;
  event_name?: string | null;
  counterparty_id?: string | null;
}

export interface GsEvent {
  schema_version: string;
  event_id: string;
  server_id: string;
  occurred_at: string;
  type: string;
  actor: Actor;
  economy?: Economy;
  subject?: Subject;
  source: Source;
}

export interface GsAlert {
  rule: string;
  severity: string;
  stage?: string;
  review_required?: boolean;
  player_id: string;
  summary: string;
  event_ids: string[];
  explain: string;
}

export interface Credentials {
  serverId: string;
  apiKey: string;
}
