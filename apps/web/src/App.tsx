import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchAlerts, fetchEvents, fetchEvidence } from './api';
import { DEMO_ALERTS, DEMO_EVENTS } from './demo';
import type { Credentials, GsAlert, GsEvent } from './types';
import './styles.css';

const LS_KEY = 'gameshield.creds';
const FILTERS = ['todo', 'dinero', 'item', 'transferencia', 'alertas'] as const;
type Filter = (typeof FILTERS)[number];

function loadCreds(): Credentials | null {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? (JSON.parse(raw) as Credentials) : null;
  } catch {
    return null;
  }
}

function timeOf(iso: string): string {
  return iso.slice(11, 19);
}

function n(value: number): string {
  return value.toLocaleString('es-CL');
}

function categoryOf(event: GsEvent): Filter {
  if (event.type.startsWith('item') || event.type.startsWith('vehicle')) return 'item';
  if (event.type === 'money.transfer') return 'transferencia';
  return 'dinero';
}

function download(name: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

function Login({ onEnter }: { onEnter: (c: Credentials, demo: boolean) => void }) {
  const [serverId, setServerId] = useState('');
  const [apiKey, setApiKey] = useState('');
  return (
    <div className="login">
      <div className="login-card">
        <div className="brand">
          <div className="mark">GS</div>
          <div>
            <b>GameShield</b>
            <span>dashboard · by Hyperium IA</span>
          </div>
        </div>
        <h1>Panel de<br />integridad</h1>
        <p className="lede">
          Ingresa la clave de tu servidor para ver la linea de tiempo economica,
          las alertas y exportar evidencia.
        </p>
        <input
          placeholder="server_id (ej: demo-rp-01)"
          value={serverId}
          onChange={(e) => setServerId(e.target.value)}
        />
        <input
          placeholder="API key (X-GS-Key)"
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
        <button
          className="btn btn-solid"
          disabled={!serverId || !apiKey}
          onClick={() => onEnter({ serverId, apiKey }, false)}
        >
          Conectar
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => onEnter({ serverId: 'demo-rp-01', apiKey: 'demo' }, true)}
        >
          Entrar en modo demo
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [creds, setCreds] = useState<Credentials | null>(loadCreds);
  const [demo, setDemo] = useState(loadCreds() === null);
  const [events, setEvents] = useState<GsEvent[]>([]);
  const [alerts, setAlerts] = useState<GsAlert[]>([]);
  const [filter, setFilter] = useState<Filter>('todo');
  const [status, setStatus] = useState<'loading' | 'live' | 'demo' | 'error'>('loading');

  const refresh = useCallback(async () => {
    if (!creds) return;
    if (demo) {
      setEvents(DEMO_EVENTS);
      setAlerts(DEMO_ALERTS);
      setStatus('demo');
      return;
    }
    try {
      const [evs, als] = await Promise.all([fetchEvents(creds), fetchAlerts(creds)]);
      setEvents(evs);
      setAlerts(als);
      setStatus('live');
    } catch {
      setEvents(DEMO_EVENTS);
      setAlerts(DEMO_ALERTS);
      setStatus('error');
    }
  }, [creds, demo]);

  useEffect(() => {
    void refresh();
    if (!demo && creds) {
      const id = setInterval(() => void refresh(), 15000);
      return () => clearInterval(id);
    }
  }, [refresh, demo, creds]);

  const flagByEvent = useMemo(() => {
    const map = new Map<string, { rule: string; severity: string }>();
    for (const alert of alerts) {
      for (const id of alert.event_ids) {
        map.set(id, { rule: alert.rule, severity: alert.severity });
      }
    }
    return map;
  }, [alerts]);

  const stats = useMemo(() => {
    const flagIds = new Set<string>();
    for (const a of alerts) {
      for (const id of a.event_ids) flagIds.add(id);
    }
    let noOrigin = 0;
    let dupeGrants = 0;
    let laundered = 0;
    for (const e of events) {
      if (!flagIds.has(e.event_id)) continue;
      const amount = e.economy?.amount ?? 0;
      if (e.type === 'money.credit') noOrigin += amount;
      if (e.type === 'item.grant' || e.type === 'vehicle.grant') dupeGrants += 1;
      if (e.type === 'money.transfer') laundered += amount;
    }
    return {
      events: events.length,
      alerts: alerts.length,
      noOrigin,
      dupeGrants,
      laundered,
    };
  }, [events, alerts]);

  const visible = useMemo(() => {
    if (filter === 'todo') return events;
    if (filter === 'alertas') return events.filter((e) => flagByEvent.has(e.event_id));
    return events.filter((e) => categoryOf(e) === filter);
  }, [events, filter, flagByEvent]);

  const onExport = async () => {
    if (demo || !creds) {
      download('gameshield-evidence-demo.json', {
        report: { server_id: 'demo-rp-01', generated_at: new Date().toISOString() },
        summary: { total_events: events.length, alert_count: alerts.length },
        alerts,
        events,
      });
      return;
    }
    try {
      const report = await fetchEvidence(creds);
      download(`gameshield-evidence-${creds.serverId}.json`, report);
    } catch {
      setStatus('error');
    }
  };

  if (!creds) {
    return (
      <Login
        onEnter={(c, isDemo) => {
          localStorage.setItem(LS_KEY, JSON.stringify(c));
          setCreds(c);
          setDemo(isDemo);
        }}
      />
    );
  }

  return (
    <div className="dash">
      <header className="topbar">
        <div className="brand">
          <div className="mark">GS</div>
          <div>
            <b>GameShield</b>
            <span>dashboard</span>
          </div>
        </div>
        <div className="top-meta">
          <span className="chip">servidor · {creds.serverId}</span>
          <span className={`chip mode-${status}`}>
            {status === 'live' && '● LIVE'}
            {status === 'demo' && '● DEMO'}
            {status === 'error' && '● MODO DEMO'}
            {status === 'loading' && '● CARGANDO'}
          </span>
          <button className="btn-mini" onClick={() => void refresh()}>Refrescar</button>
          <button
            className="btn-mini"
            onClick={() => {
              localStorage.removeItem(LS_KEY);
              setCreds(null);
            }}
          >
            Salir
          </button>
        </div>
      </header>

      <section className="stats">
        <div className="stat">
          <div className="big">{n(stats.events)}</div>
          <div className="lbl">eventos registrados</div>
        </div>
        <div className="stat">
          <div className="big red">{n(stats.alerts)}</div>
          <div className="lbl">alertas activas</div>
        </div>
        <div className="stat">
          <div className="big red">{n(stats.noOrigin)}</div>
          <div className="lbl">dinero sin origen</div>
        </div>
        <div className="stat">
          <div className="big red">{n(stats.dupeGrants)}x</div>
          <div className="lbl">concesiones duplicadas</div>
        </div>
        <div className="stat">
          <div className="big amber">{n(stats.laundered)}</div>
          <div className="lbl">movidos en cadena</div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Alertas</h2>
          <button className="btn-mini accent" onClick={() => void onExport()}>
            Exportar evidencia (JSON)
          </button>
        </div>
        <div className="alerts">
          {alerts.length === 0 && <p className="empty">Sin alertas en la ventana analizada.</p>}
          {alerts.map((a, i) => (
            <article key={`${a.rule}-${i}`} className={`alert-card ${a.severity}`}>
              <div className="alert-top">
                <span className={`sev ${a.severity}`}>
                  {a.severity === 'high' ? 'Severidad alta' : 'Severidad media'}
                </span>
                {a.stage && (
                  <span className={`sev stage-${a.stage}`}>
                    {a.stage === 'anomaly' ? 'Anomalia' : 'Sospecha'}
                  </span>
                )}
                <span className="rule-name">{a.rule}</span>
                <span className="alert-count">{a.event_ids.length} evento(s)</span>
              </div>
              <h3>{a.summary}</h3>
              <p className="explain">{a.explain}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Linea de tiempo economica</h2>
          <div className="filters">
            {FILTERS.map((f) => (
              <button
                key={f}
                className={`filter ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="timeline">
          {visible.map((e) => {
            const flag = flagByEvent.get(e.event_id);
            const amt = e.economy?.amount;
            const amount =
              amt !== null && amt !== undefined ? n(amt) : e.subject?.sku ?? '—';
            return (
              <div key={e.event_id} className={`tl-entry ${flag ? `flag-${flag.severity}` : ''}`}>
                <div className="tl-time">{timeOf(e.occurred_at)}</div>
                <div className="tl-main">
                  <div className="type">{e.type}</div>
                  <div className="who">
                    {e.actor.player_id} <span>"{e.actor.display_name ?? 'sin nombre'}"</span>
                  </div>
                  <div className="detail">
                    {e.source.resource} · {e.source.event_name ?? '—'}
                    {e.source.counterparty_id ? ` -> ${e.source.counterparty_id}` : ''}
                  </div>
                  {flag && (
                    <div className="tags">
                      <span className={`tag-chip ${flag.severity === 'high' ? '' : 'med'}`}>
                        {flag.rule}
                      </span>
                    </div>
                  )}
                </div>
                <div className={`tl-amount ${flag ? (flag.severity === 'high' ? 'hot' : 'warm') : ''}`}>
                  {amount}
                  <span className="cur">{e.economy?.currency ?? e.subject?.kind ?? ''}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <footer className="foot">
        GameShield by Hyperium IA · evidencia con firma HMAC-SHA256 · software propietario
      </footer>
    </div>
  );
}
