import type { Credentials, GsAlert, GsEvent } from './types';

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '';

async function call<T>(path: string, creds: Credentials, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      'X-GS-Key': creds.apiKey,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}`);
  }
  return (await res.json()) as T;
}

export function fetchEvents(creds: Credentials): Promise<GsEvent[]> {
  return call<{ events: GsEvent[] }>(
    `/v1/servers/${encodeURIComponent(creds.serverId)}/events?limit=500`,
    creds,
  ).then((r) => r.events);
}

export function fetchAlerts(creds: Credentials): Promise<GsAlert[]> {
  return call<{ alerts: GsAlert[] }>(
    `/v1/servers/${encodeURIComponent(creds.serverId)}/alerts`,
    creds,
  ).then((r) => r.alerts);
}

export function fetchEvidence(creds: Credentials): Promise<unknown> {
  return call(`/v1/servers/${encodeURIComponent(creds.serverId)}/evidence`, creds, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
