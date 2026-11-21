import type { GsAlert, GsEvent } from './types';

const T = '2026-11-20T';

function ev(
  id: string,
  time: string,
  type: string,
  player: string,
  name: string,
  resource: string,
  eventName: string,
  extra: Partial<GsEvent> = {},
): GsEvent {
  const base: GsEvent = {
    schema_version: '1',
    event_id: `22222222-2222-4222-8222-2222222222${id}`,
    server_id: 'demo-rp-01',
    occurred_at: `${T}${time}Z`,
    type,
    actor: { player_id: player, display_name: name, role: 'player' },
    source: { resource, event_name: eventName },
  };
  return { ...base, ...extra } as GsEvent;
}

export const DEMO_EVENTS: GsEvent[] = [
  ev('01', '09:58:00', 'sale', 'p-007', 'Lucia', 'qb-shops', 'shop:sell', {
    economy: { currency: 'USD', amount: 4200 },
  }),
  ev('02', '09:58:01', 'money.credit', 'p-007', 'Lucia', 'qb-shops', 'shop:sell', {
    economy: { currency: 'USD', amount: 4200 },
  }),
  ev('03', '10:05:00', 'money.credit', 'p-042', 'DupeR', 'unknown', 'external', {
    economy: { currency: 'USD', amount: 250000 },
  }),
  ev('04', '10:05:02', 'item.grant', 'p-042', 'DupeR', 'qb-garages', 'garage:store', {
    subject: { kind: 'item', sku: 'SULTAN_RS', quantity: 1 },
  }),
  ev('05', '10:05:07', 'item.grant', 'p-042', 'DupeR', 'qb-garages', 'garage:store', {
    subject: { kind: 'item', sku: 'SULTAN_RS', quantity: 1 },
  }),
  ev('06', '10:05:12', 'item.grant', 'p-042', 'DupeR', 'qb-garages', 'garage:store', {
    subject: { kind: 'item', sku: 'SULTAN_RS', quantity: 1 },
  }),
  ev('07', '10:05:17', 'item.grant', 'p-042', 'DupeR', 'qb-garages', 'garage:store', {
    subject: { kind: 'item', sku: 'SULTAN_RS', quantity: 1 },
  }),
  ev('08', '10:05:22', 'item.grant', 'p-042', 'DupeR', 'qb-garages', 'garage:store', {
    subject: { kind: 'item', sku: 'SULTAN_RS', quantity: 1 },
  }),
  ev('09', '10:06:00', 'money.transfer', 'p-042', 'DupeR', 'qb-banking', 'bank:transfer', {
    economy: { currency: 'USD', amount: 240000 },
    source: { resource: 'qb-banking', event_name: 'bank:transfer', counterparty_id: 'p-043' },
  }),
  ev('10', '10:06:40', 'money.transfer', 'p-043', 'Mule1', 'qb-banking', 'bank:transfer', {
    economy: { currency: 'USD', amount: 238000 },
    source: { resource: 'qb-banking', event_name: 'bank:transfer', counterparty_id: 'p-044' },
  }),
  ev('11', '10:07:10', 'money.transfer', 'p-044', 'Mule2', 'qb-banking', 'bank:transfer', {
    economy: { currency: 'USD', amount: 237500 },
    source: { resource: 'qb-banking', event_name: 'bank:transfer', counterparty_id: 'p-045' },
  }),
];

export const DEMO_ALERTS: GsAlert[] = [
  {
    rule: 'money_without_origin',
    stage: 'suspicion',
    severity: 'high',
    player_id: 'p-042',
    summary: 'p-042 recibió 250.000 sin origen económico',
    event_ids: ['22222222-2222-4222-8222-222222222203'],
    explain:
      'Ninguna venta, trueque o transferencia entrante de p-042 en los 600 s previos justifica un crédito de 250.000.',
  },
  {
    rule: 'cascade_dupes',
    stage: 'suspicion',
    severity: 'high',
    player_id: 'p-042',
    summary: '5 concesiones idénticas de SULTAN_RS en 20 segundos',
    event_ids: [
      '22222222-2222-4222-8222-222222222204',
      '22222222-2222-4222-8222-222222222205',
      '22222222-2222-4222-8222-222222222206',
      '22222222-2222-4222-8222-222222222207',
      '22222222-2222-4222-8222-222222222208',
    ],
    explain:
      'La misma concesión (item.grant de SULTAN_RS cantidad 1) se repite 5 veces en 20 s con el mismo origen — patrón compatible con explotación de duplicación; requiere revisión del staff.',
  },
  {
    rule: 'chained_transfers',
    stage: 'anomaly',
    severity: 'medium',
    player_id: 'p-042',
    summary: 'Cadena de 3 transferencias moviendo casi el mismo monto',
    event_ids: [
      '22222222-2222-4222-8222-222222222209',
      '22222222-2222-4222-8222-222222222210',
      '22222222-2222-4222-8222-222222222211',
    ],
    explain:
      '3 saltos encadenados de money.transfer moviendo casi el mismo monto (±1%) con menos de 120 s por salto — posible lavado o embudo coordinado.',
  },
];
