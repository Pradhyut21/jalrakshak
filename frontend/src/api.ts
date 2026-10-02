export type RiskStatus = 'SAFE' | 'WATCH' | 'ACT_NOW' | 'UNKNOWN';
export interface Site {
  id: string; name: string; location: string; capacity_l: number; reserve_l: number;
  lead_hours: number; buffer_hours: number; freshness_minutes: number;
}
export interface Analysis {
  status: RiskStatus; current_rate_lph: number | null; baseline_rate_lph: number | null;
  reserve_breach_at: string | null; empty_at: string | null; conservative_breach_at: string | null;
  latest_action_at: string | null; hours_to_reserve: number | null; action_margin_hours: number | null;
  next_supply_at: string | null; supply_status: string;
  anomaly: { active: boolean; observed_rate_lph: number | null; expected_rate_lph: number | null; ratio: number | null; evidence_count: number; reason: string };
  recommendation: { type: string; title: string; body: string; deadline: string | null };
  facts: string[]; method: string; uncertainty_label: string;
  history: { at: string; volume_l: number; rate_lph: number | null }[];
  projection: { at: string; volume_l: number; conservative_l: number; optimistic_l: number }[];
  shortage_hours: number | null; unmet_demand_l: number | null; overflow_l: number | null;
}
export interface Action {
  id: string; type: string; status: string; created_at: string; approved_at: string | null;
  published_at: string | null; receipt_at: string | null; evidence_version: number;
  message: string; destination: string;
}
export interface Incident {
  id: string; status: string; opened_at: string; intervention_at: string | null;
  verified_at: string | null; verification_count: number; reason: string;
}
export interface Dashboard {
  site: Site; clock: string; mode: string; version: number; csrf_token: string;
  state: { volume_l: number; percentage: number; observed_at: string; source: string; simulated: boolean; data_state: string };
  analysis: Analysis; incident: Incident | null; actions: Action[];
  events: { id: string; at: string; kind: string; title: string; detail: string }[];
  evaluation: Record<string, unknown>;
}
export interface Preview { analysis: Analysis; before: unknown; summary: string; simulated: boolean }
export interface AssistantAnswer { answer: string; facts: unknown[]; provider: string; simulated: boolean }

let csrfToken = '';
const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ?? '';

export async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${apiBase}/api${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    credentials: 'include',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(20000),
  });
  const value: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = value && typeof value === 'object' && 'detail' in value ? value.detail : null;
    const message = typeof detail === 'string' ? detail : detail ? JSON.stringify(detail) : `Request failed (${response.status}).`;
    throw new Error(message);
  }
  if (value === null) throw new Error('The server returned an empty response.');
  if (typeof value === 'object' && 'csrf_token' in value && typeof value.csrf_token === 'string') csrfToken = value.csrf_token;
  return value as T;
}
