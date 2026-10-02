import { useEffect, useId, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BookOpen, Check,
  CheckCircle2, ChevronRight, Clock3, Database, Droplets, FlaskConical,
  Gauge, Info, LayoutDashboard, MapPin, Plus, RefreshCw, Send, ShieldCheck,
  SlidersHorizontal, Truck, Waves, Wrench, X, AlertTriangle,
} from 'lucide-react';
import { request } from './api';
import type { Action, Analysis, AssistantAnswer, Dashboard, Preview, RiskStatus } from './api';

const numbers = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 });
function num(value: number | null | undefined, fractional = false) {
  return value == null || !Number.isFinite(value) ? '—' : (fractional ? decimal : numbers).format(value);
}
function time(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', hour: 'numeric', minute: '2-digit', hour12: true }).format(new Date(value)) : 'Not available';
}
function date(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', weekday: 'short' }).format(new Date(value)) : 'No crossing forecast';
}
function shortDate(value: string) {
  return new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short' }).format(new Date(value));
}
function record(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
function numeric(value: unknown): number | null { return typeof value === 'number' && Number.isFinite(value) ? value : null; }
function title(value: string) { return value.replaceAll('_', ' ').toLowerCase().replace(/^\w/, c => c.toUpperCase()); }
function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'Something went wrong. Please retry.'; }

const statusLabels: Record<RiskStatus, string> = { SAFE: 'Reserve outlook stable', WATCH: 'Keep an eye on supply', ACT_NOW: 'Action needed now', UNKNOWN: 'More evidence needed' };
type View = 'overview' | 'activity' | 'evidence';
type Modal = 'preview' | 'reading' | 'reset' | null;

function Badge({ children, tone = 'green' }: { children: ReactNode; tone?: string }) {
  return <span className={`badge ${tone}`}><span className="badge-dot" />{children}</span>;
}

function Dialog({ title: label, children, close, wide = false }: { title: string; children: ReactNode; close: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return <dialog ref={ref} className={`dialog ${wide ? 'wide' : ''}`} aria-labelledby={id} onCancel={event => { event.preventDefault(); close(); }}>
    <div className="dialog-heading"><h2 id={id}>{label}</h2><button className="icon-button" aria-label="Close dialog" onClick={close}><X size={20} /></button></div>
    {children}
  </dialog>;
}

function Tank({ dashboard }: { dashboard: Dashboard }) {
  const id = useId().replaceAll(':', '');
  const { site, state } = dashboard;
  const fill = Math.max(0, Math.min(100, state.percentage));
  const waterY = 188 - fill * 1.4;
  const reserveY = 188 - (site.reserve_l / site.capacity_l) * 140;
  return <div className="tank-illustration">
    <svg viewBox="0 0 280 245" role="img" aria-label={`Tank ${num(state.percentage, true)} percent full. ${num(state.volume_l)} litres observed; reserve ${num(site.reserve_l)} litres.`}>
      <defs>
        <linearGradient id={`water-${id}`} x1="0" y1="0" x2="0.8" y2="1"><stop stopColor="#91c5b8" /><stop offset="1" stopColor="#418978" /></linearGradient>
        <linearGradient id={`body-${id}`} x1="0" x2="1"><stop stopColor="#f1f8ef" /><stop offset="1" stopColor="#d7e6d3" /></linearGradient>
        <clipPath id={`clip-${id}`}><path d="M62 49 Q62 28 140 28 Q218 28 218 49 L218 185 Q218 208 140 208 Q62 208 62 185Z" /></clipPath>
      </defs>
      <ellipse cx="143" cy="218" rx="93" ry="13" fill="#d9e5d3" />
      <path d="M62 49 Q62 28 140 28 Q218 28 218 49 L218 185 Q218 208 140 208 Q62 208 62 185Z" fill={`url(#body-${id})`} stroke="#93b3a2" strokeWidth="1.4" />
      <g clipPath={`url(#clip-${id})`}>
        <path d={`M53 ${waterY} Q100 ${waterY - 10} 142 ${waterY} T227 ${waterY} L227 218 L53 218Z`} fill={`url(#water-${id})`} />
        <path d={`M52 ${waterY + 7} Q100 ${waterY + 18} 147 ${waterY + 7} T228 ${waterY + 7}`} fill="none" stroke="#ffffff" strokeOpacity=".28" strokeWidth="2" />
        <path d="M75 60 V181" stroke="white" strokeOpacity=".3" strokeWidth="5" strokeLinecap="round" />
      </g>
      <ellipse cx="140" cy="48" rx="78" ry="21" fill="#e4eee0" stroke="#93b3a2" strokeWidth="1.4" />
      <ellipse cx="140" cy="47" rx="57" ry="12" fill="#d4e4cd" />
      <path d="M120 34 V26 Q120 21 128 21 H151 Q159 21 159 26 V34" stroke="#79998a" strokeWidth="3" fill="#e4eee0" />
      <line x1="48" y1={reserveY} x2="240" y2={reserveY} stroke="#ac6b38" strokeWidth="1.4" strokeDasharray="4 4" />
      <circle cx="239" cy={reserveY} r="3" fill="#ac6b38" />
      <path d="M216 158 H234 V183" fill="none" stroke="#668879" strokeWidth="9" strokeLinecap="round" />
      <path d="M216 158 H234 V183" fill="none" stroke="#acc6af" strokeWidth="5" strokeLinecap="round" />
      <text x="140" y="119" textAnchor="middle" fill="#173d37" fontSize="35" fontWeight="650">{num(state.percentage, true)}%</text>
      <text x="140" y="139" textAnchor="middle" fill="#173d37" fontSize="10" fontWeight="600" letterSpacing="1.6">OBSERVED LEVEL</text>
    </svg>
    <span className="tank-caption"><span className="reserve-key" />Reserve · {num(site.reserve_l)} L</span>
  </div>;
}

function ProjectionChart({ dashboard, analysis = dashboard.analysis }: { dashboard: Dashboard; analysis?: Analysis }) {
  const uid = useId().replaceAll(':', '');
  const history = analysis.history ?? [];
  const projected = analysis.projection ?? [];
  const historyShown = history.slice(-24);
  const allTimes = [...historyShown, ...projected].map(point => new Date(point.at).getTime()).filter(Number.isFinite);
  if (!allTimes.length || !projected.length) return <div className="chart-empty"><Activity size={30} /><p>More readings are needed for a projection.</p></div>;
  const min = Math.min(...allTimes);
  const max = Math.max(...allTimes, min + 3600000);
  const width = 780, height = 265;
  const left = 56, right = 56, top = 20, bottom = 65;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const x = (at: string) => left + (new Date(at).getTime() - min) / (max - min) * plotWidth;
  const y = (volume: number) => top + (1 - Math.max(0, Math.min(dashboard.site.capacity_l, volume)) / dashboard.site.capacity_l) * plotHeight;
  const line = (points: { at: string; volume_l: number }[]) => points.map((point, i) => `${i ? 'L' : 'M'}${x(point.at).toFixed(2)},${y(point.volume_l).toFixed(2)}`).join(' ');
  const conservative = projected.map(point => ({ at: point.at, volume_l: point.conservative_l }));
  const optimistic = projected.map(point => ({ at: point.at, volume_l: point.optimistic_l }));
  const envelope = `${line(optimistic)} ${conservative.slice().reverse().map(point => `L${x(point.at).toFixed(2)},${y(point.volume_l).toFixed(2)}`).join(' ')} Z`;
  const nowX = x(dashboard.clock);
  const supplyAt = analysis.next_supply_at;
  const showSupply = supplyAt && new Date(supplyAt).getTime() >= min && new Date(supplyAt).getTime() <= max;
  return <div className="projection-chart">
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Observed and projected tank storage in litres, with conservative sensitivity and reserve threshold. All values are simulated.">
      <defs><linearGradient id={`shade-${uid}`} x1="0" y1="0" x2="0" y2="1"><stop stopColor="#d1e6d8" stopOpacity=".8" /><stop offset="1" stopColor="#e9f0e8" stopOpacity=".16" /></linearGradient></defs>
      {[0, 0.25, 0.5, 0.75, 1].map(ratio => <g key={ratio}>
        <line x1={left} x2={width - right} y1={y(ratio * dashboard.site.capacity_l)} y2={y(ratio * dashboard.site.capacity_l)} stroke="#e4e9e2" strokeDasharray={ratio === 0 ? undefined : '3 4'} />
        <text x={left - 12} y={y(ratio * dashboard.site.capacity_l) + 4} textAnchor="end" className="chart-text">{num(ratio * dashboard.site.capacity_l / 1000)}k</text>
      </g>)}
      <path d={envelope} fill={`url(#shade-${uid})`} />
      <line x1={left} x2={width - right} y1={y(dashboard.site.reserve_l)} y2={y(dashboard.site.reserve_l)} stroke="#bf875a" strokeDasharray="5 5" />
      <text x={width - right} y={y(dashboard.site.reserve_l) - 7} textAnchor="end" className="chart-text reserve-text">Reserve {num(dashboard.site.reserve_l)} L</text>
      {nowX >= left && nowX <= width - right && <><line x1={nowX} x2={nowX} y1={top} y2={height - bottom} stroke="#9aac9e" strokeDasharray="3 4" /><text x={Math.min(nowX + 7, width - 85)} y={top + 11} className="chart-text">Now</text></>}
      {showSupply && <><line x1={x(supplyAt)} x2={x(supplyAt)} y1={top + 18} y2={height - bottom} stroke="#8bb4a7" strokeDasharray="3 4" /><text x={Math.min(x(supplyAt) + 6, width - 210)} y={top + 32} className="chart-text">Planned supply</text></>}
      <path d={line(historyShown)} fill="none" stroke="#203f36" strokeWidth="2.7" strokeLinejoin="round" />
      <path d={line(projected)} fill="none" stroke="#438974" strokeWidth="2.5" strokeLinejoin="round" />
      <path d={line(conservative)} fill="none" stroke="#b87545" strokeWidth="1.8" strokeDasharray="5 4" />
      {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
        const at = new Date(min + ratio * (max - min)).toISOString();
        return <text key={ratio} x={left + ratio * plotWidth} y={height - 34} textAnchor="middle" className={`chart-text tick-label ${ratio === 0.25 || ratio === 0.75 ? 'tick-secondary' : ''}`}><tspan x={left + ratio * plotWidth}>{time(at)}</tspan><tspan className="tick-date" x={left + ratio * plotWidth} dy="25">{shortDate(at)}</tspan></text>;
      })}
    </svg>
    <div className="chart-legend"><span><i className="line-key observed" />Observed</span><span><i className="line-key central" />Planned-supply projection</span><span><i className="line-key conservative" />Conservative</span><span className="legend-unit">Litres · IST</span></div>
  </div>;
}

function Timeline({ dashboard, compact = false }: { dashboard: Dashboard; compact?: boolean }) {
  const events = [...dashboard.events].reverse();
  const visible = compact ? events.slice(0, 5) : events;
  return <div className="timeline">{visible.length ? visible.map((event, index) => <div className="timeline-entry" key={event.id}>
    <span className={`timeline-icon ${event.kind.toLowerCase().includes('verif') ? 'complete' : ''}`}>{event.kind.toLowerCase().includes('verif') ? <Check size={13} /> : <span />}</span>
    <div className="timeline-content"><div className="timeline-title"><strong>{event.title}</strong><time>{time(event.at)}</time></div><p>{event.detail}</p>{!compact && <span className="tiny-label">{date(event.at)} · {title(event.kind)}</span>}</div>
    {index < visible.length - 1 && <i className="timeline-connector" />}
  </div>) : <div className="empty-state"><Activity size={24} /><p>No events recorded yet.</p></div>}</div>;
}

function IncidentProgress({ dashboard }: { dashboard: Dashboard }) {
  const { incident, actions } = dashboard;
  const notified = actions.some(action => ['LOCAL_RECEIVED', 'PUBLISHED'].includes(action.status));
  const steps = [
    { label: 'Detected', active: !!incident },
    { label: 'Request approved', active: notified || actions.some(action => action.approved_at) },
    { label: 'New observations', active: !!incident?.intervention_at && dashboard.analysis.history.some(point => new Date(point.at).getTime() > new Date(incident.intervention_at!).getTime()) },
    { label: 'Verified recovery', active: incident?.status === 'RESOLVED' },
  ];
  return <div className="incident-progress">{steps.map((step, index) => <div className={`progress-step ${step.active ? 'complete' : ''}`} key={step.label}><span>{step.active ? <Check size={14} /> : index + 1}</span><small>{step.label}</small></div>)}</div>;
}

function Evaluation({ dashboard }: { dashboard: Dashboard }) {
  const [evaluation, setEvaluation] = useState<Record<string, unknown>>(dashboard.evaluation);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { setEvaluation(dashboard.evaluation); }, [dashboard.evaluation]);
  const refresh = async () => {
    setLoading(true); setError('');
    try { setEvaluation(await request<Record<string, unknown>>('/evaluation')); } catch (err) { setError(errorMessage(err)); } finally { setLoading(false); }
  };
  const scalar = Object.entries(evaluation).filter(([, value]) => typeof value === 'number' || typeof value === 'string' || typeof value === 'boolean');
  const finalTest = record(evaluation.final_test);
  const selected = record(finalTest.recent_mean_selected);
  const lastRate = record(finalTest.last_rate);
  const selection = record(evaluation.selection);
  const target = record(evaluation.target);
  const testSplit = record(record(evaluation.splits).test);
  const anomalyTest = record(evaluation.anomaly_final_test);
  const reserveTiming = record(evaluation.reserve_timing);
  const hasResults = numeric(selected.mae_l) !== null;
  return <div className="evidence-page">
    <section className="card evidence-intro"><div className="card-heading"><div><span className="eyebrow">PROOF, NOT PROMISES</span><h2>Every claim needs evidence.</h2></div><Badge tone="neutral">Simulated evaluation</Badge></div><p>These results describe this prototype and its simulated history. They do not establish real-world reliability, confirmed leaks, or measured water savings.</p></section>
    <section className="card"><div className="card-heading"><div><h3>Evaluation artifact</h3><p className="muted">Values returned by the API; missing results remain pending.</p></div><button className="button secondary small" disabled={loading} onClick={() => void refresh()}><RefreshCw size={14} className={loading ? 'spin' : ''} />Refresh</button></div>
      {error && <p className="inline-error" role="alert">{error}</p>}
      {hasResults && <div className="evaluation-results"><div className="evaluation-metric-grid"><div><span>Selected method · demand MAE</span><strong>{num(numeric(selected.mae_l), true)} <small>L</small></strong><p>{num(numeric(target.horizon_hours), true)}-hour prediction horizon</p></div><div><span>Last-rate baseline · demand MAE</span><strong>{num(numeric(lastRate.mae_l), true)} <small>L</small></strong><p>Reported even when equally good</p></div><div><span>Final-test origins</span><strong>{num(numeric(selected.samples))}</strong><p>{typeof testSplit.first_origin === 'string' ? shortDate(testSplit.first_origin) : 'Unknown start'} – {typeof testSplit.last_origin === 'string' ? shortDate(testSplit.last_origin) : 'Unknown end'}</p></div><div><span>Labeled abnormal-use episodes</span><strong>{num(numeric(anomalyTest.labeled_episodes))}</strong><p>{num(numeric(anomalyTest.missed_episodes))} missed · {num(numeric(anomalyTest.false_alert_events))} false alert events</p></div></div>
        <p className="evaluation-interpretation">{typeof selection.interpretation === 'string' ? selection.interpretation : 'Method selection and interpretation are recorded in the full artifact.'}</p>
        <div className="evaluation-table-wrap"><table className="evaluation-table"><caption>Final-test demand errors · simulated litres</caption><thead><tr><th scope="col">Method</th><th scope="col">MAE (L)</th><th scope="col">RMSE (L)</th><th scope="col">Origins</th></tr></thead><tbody>{Object.entries(finalTest).map(([method, values]) => { const metrics = record(values); return <tr key={method}><th scope="row">{title(method)}</th><td>{num(numeric(metrics.mae_l), true)}</td><td>{num(numeric(metrics.rmse_l), true)}</td><td>{num(numeric(metrics.samples))}</td></tr>; })}</tbody></table></div>
        {typeof reserveTiming.reason === 'string' && <div className="evaluation-limitation"><Info size={16} /><p><strong>Reserve timing is not evaluated by these metrics.</strong> {reserveTiming.reason}</p></div>}
      </div>}
      <dl className="artifact-values">{scalar.map(([key, value]) => <div key={key}><dt>{title(key)}</dt><dd>{typeof value === 'number' ? num(value, true) : String(value)}</dd></div>)}</dl>
      <details className="raw-artifact"><summary>Inspect the complete artifact <ChevronRight size={14} /></summary><pre>{JSON.stringify(evaluation, null, 2)}</pre></details>
    </section>
    <div className="evidence-grid"><section className="card"><div className="section-icon"><Database size={21} /></div><h3>Data provenance</h3><dl className="detail-list"><div><dt>Current source</dt><dd>{title(dashboard.state.source)}</dd></div><div><dt>Observation</dt><dd>{date(dashboard.state.observed_at)} · {time(dashboard.state.observed_at)} IST</dd></div><div><dt>Freshness</dt><dd>{title(dashboard.state.data_state)}</dd></div><div><dt>Forecast method</dt><dd>{title(dashboard.analysis.method)}</dd></div><div><dt>Evidence version</dt><dd>{dashboard.version}</dd></div></dl></section>
      <section className="card"><div className="section-icon"><ShieldCheck size={21} /></div><h3>What this prototype verifies</h3><ul className="honesty-list"><li>Fresh readings support an updated reserve forecast.</li><li>A local notification receipt confirms a demo message, not a tanker booking.</li><li>Recovery requires subsequent observations; a repair claim is insufficient.</li><li>No sensor deployment, live cloud execution or medical safety is implied.</li></ul></section></div>
  </div>;
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [view, setView] = useState<View>('overview');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [modal, setModal] = useState<Modal>(null);
  const [approval, setApproval] = useState<Action | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [delayHours, setDelayHours] = useState(6);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [answerVersion, setAnswerVersion] = useState<number | null>(null);
  const [volume, setVolume] = useState('');
  const loadingRef = useRef(false);

  const perform = async (label: string, action: () => Promise<void>) => {
    setBusy(label); setError(''); setNotice('');
    try { await action(); } catch (err) { setError(errorMessage(err)); } finally { setBusy(''); }
  };
  const refresh = async () => {
    const value = await request<Dashboard>('/dashboard');
    setDashboard(value);
    return value;
  };
  useEffect(() => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    void perform('Loading workspace', async () => { await refresh(); });
  }, []);
  useEffect(() => { setPreview(null); }, [dashboard?.version]);

  const changeScenario = (scenario: 'excess_usage' | 'repair' | 'delivery') => void perform('Updating demo', async () => {
    setDashboard(await request<Dashboard>('/demo/scenario', { scenario, hours: 2 }));
    setNotice('Demo observations updated. The forecast and incident state were recomputed by the server.');
  });
  const runPreview = () => void perform('Computing preview', async () => {
    setPreview(await request<Preview>('/simulate', { delay_hours: delayHours, added_supply_l: 0, demand_change_percent: 0 }));
  });
  const propose = () => void perform('Preparing request', async () => {
    const action = await request<Action>('/actions/propose', { type: 'REQUEST_SUPPLY' });
    await refresh(); setConfirmed(false); setApproval(action);
  });
  const approve = () => {
    if (!approval || !confirmed) return;
    void perform('Recording approval', async () => {
      const next = await request<Dashboard>(`/actions/${encodeURIComponent(approval.id)}/approve`, { evidence_version: approval.evidence_version, confirmed: true });
      setDashboard(next); setApproval(null);
      setNotice('Approval recorded. See the action status below for the actual notification result. This does not book supply.');
    });
  };
  const ask = (question: 'deadline' | 'delay' | 'buffer') => void perform('Reading evidence', async () => {
    setAnswer(await request<AssistantAnswer>('/assistant', { question }));
    setAnswerVersion(dashboard?.version ?? null);
  });
  const submitReading = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!dashboard) return;
    void perform('Saving demo reading', async () => {
      setDashboard(await request<Dashboard>('/readings', { reading_id: crypto.randomUUID(), observed_at: new Date(new Date(dashboard.clock).getTime() + 30 * 60000).toISOString(), volume_l: Number(volume), source: 'manual_demo', simulated: true, advance_clock: true }));
      setModal(null); setVolume(''); setNotice('Manual demo observation saved. Its source remains visibly simulated.');
    });
  };
  const navigation: { id: View; label: string; icon: ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'activity', label: 'Incident history', icon: <Activity size={18} /> },
    { id: 'evidence', label: 'Evidence & evaluation', icon: <BookOpen size={18} /> },
  ];
  const isBusy = !!busy;
  const a = dashboard?.analysis;
  const risk = a?.status ?? 'UNKNOWN';
  const activeIncident = dashboard?.incident && dashboard.incident.status !== 'RESOLVED';
  const lastAction = dashboard?.actions.at(-1);
  const modalError = error && (modal || approval);

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={event => { event.preventDefault(); setView('overview'); }} aria-label="JalRakshak overview"><span className="brand-mark"><Droplets size={24} strokeWidth={1.7} /></span><span>JalRakshak<small>CARE FOR EVERY DROP</small></span></a>
      <div className="workspace-name"><span className="eyebrow">YOUR WORKSPACE</span><div><span className="workspace-avatar">A</span><span>{dashboard?.site.name ?? 'Water operations'}<small>Single-site demo</small></span></div></div>
      <nav aria-label="Main navigation">{navigation.map(item => <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} onClick={() => setView(item.id)} aria-current={view === item.id ? 'page' : undefined}>{item.icon}<span>{item.label}</span>{view === item.id && <span className="nav-dot" />}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-note"><Waves size={25} /><p>Small signals.<br />Better decisions.</p><small>Know when to act before the reserve runs low.</small></div><div className="profile"><span className="profile-avatar">C</span><div>Caretaker workspace<small>Isolated local demo session</small></div></div></div>
    </aside>

    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={13} /><span>{navigation.find(item => item.id === view)?.label}</span></div><div className="topbar-right"><span className="demo-tag"><FlaskConical size={13} />SIMULATED DEMO</span><button className="icon-button" aria-label="Refresh dashboard" disabled={isBusy} onClick={() => void perform('Refreshing', async () => { await refresh(); })}><RefreshCw size={17} className={busy === 'Refreshing' ? 'spin' : ''} /></button></div></header>
      <main id="main-content">
        <div className="page-heading"><div><div className="eyebrow">A LITTLE FORESIGHT GOES A LONG WAY</div><h1>{view === 'overview' ? 'Water, without the worry.' : view === 'activity' ? 'A record of every decision.' : 'Evidence you can inspect.'}</h1><p>{dashboard ? <><MapPin size={13} />{dashboard.site.name}<span className="dot-separator">·</span>{dashboard.site.location}</> : 'Connecting to your water operations workspace.'}</p></div><div className="simulation-clock"><Clock3 size={15} /><div><span>Demo clock · IST</span><strong>{dashboard ? `${date(dashboard.clock)}, ${time(dashboard.clock)}` : 'Waiting for server'}</strong></div></div></div>

        <div className="provenance-banner"><Info size={15} /><span>This is a local prototype with simulated readings. Scenario actions update the demo tank; notifications create local demo receipts.</span><span className="banner-label">NO REAL TANK CONNECTED</span></div>
        {error && !modalError && <div className="alert-banner error" role="alert"><AlertTriangle size={17} /><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
        {notice && <div className="alert-banner success" role="status"><CheckCircle2 size={17} /><span>{notice}</span><button aria-label="Dismiss notice" onClick={() => setNotice('')}><X size={16} /></button></div>}

        {!dashboard ? <section className="card connection-state"><span className="connection-icon"><Droplets size={34} /></span><h2>{busy ? 'Getting the full picture…' : 'Your workspace is waiting.'}</h2><p>{busy ? 'Loading tank observations and server-computed evidence.' : 'Start the local API, then reconnect. No readings or forecast values are invented while the server is unavailable.'}</p><button className="button primary" disabled={isBusy} onClick={() => void perform('Loading workspace', async () => { await refresh(); })}><RefreshCw size={16} className={isBusy ? 'spin' : ''} />{busy || 'Reconnect'}</button></section>
          : view === 'evidence' ? <Evaluation dashboard={dashboard} />
          : view === 'activity' ? <div className="activity-page"><section className="card"><div className="card-heading"><div><span className="eyebrow">THE INCIDENT LOOP</span><h2>{dashboard.incident ? title(dashboard.incident.status) : 'No active incident'}</h2></div><Badge tone={dashboard.incident?.status === 'RESOLVED' ? 'green' : 'neutral'}>{dashboard.incident?.status === 'RESOLVED' ? 'Recovery verified' : 'Simulated record'}</Badge></div><IncidentProgress dashboard={dashboard} /><p className="muted">{dashboard.incident?.reason ?? 'The system records observations, recommendations and actions here as the demo progresses.'}</p></section><section className="card"><div className="card-heading"><h3>Event history</h3><span className="tiny-label">{dashboard.events.length} recorded events</span></div><Timeline dashboard={dashboard} /></section><ActionRecords dashboard={dashboard} /></div>
          : <>
            <div className="overview-top">
              <section className={`tank-card risk-${risk.toLowerCase()}`}>
                <div className="tank-copy"><div className="tank-card-head"><span className="eyebrow">YOUR WATER RESERVE</span><Badge tone={risk === 'ACT_NOW' ? 'orange' : risk === 'UNKNOWN' ? 'neutral' : 'green'}>{statusLabels[risk]}</Badge></div><h2>{num(dashboard.state.volume_l)}<span>litres in the tank</span></h2><p>Observed storage · {num(dashboard.site.capacity_l)} L capacity</p><div className="tank-mini-stats"><div><span>Observed at</span><strong>{time(dashboard.state.observed_at)} IST</strong></div><div><span>Reading state</span><strong className={dashboard.state.data_state === 'fresh' ? 'green-text' : 'orange-text'}><span className="mini-dot" />{title(dashboard.state.data_state)}</strong></div></div><span className="source-label"><FlaskConical size={12} />{dashboard.state.simulated ? 'Simulated' : 'Manual observation'} · {title(dashboard.state.source)}</span></div><Tank dashboard={dashboard} />
              </section>
              <section className={`card deadline-card ${risk === 'ACT_NOW' ? 'urgent' : ''}`}><span className="circle-icon"><Clock3 size={21} /></span><div className="eyebrow">LATEST TIME TO START SUPPLY ACTION</div><h2>{a?.latest_action_at ? time(a.latest_action_at) : 'Not available'}<span>{date(a?.latest_action_at)}</span></h2><p>{a?.action_margin_hours != null ? a.action_margin_hours <= 0 ? `The deadline is overdue by ${num(Math.abs(a.action_margin_hours), true)} hours.` : `${num(a.action_margin_hours, true)} hours of action margin remain.` : 'More usable evidence is needed to calculate a deadline.'}</p><div className="deadline-formula"><span>{num(dashboard.site.lead_hours)}h supply lead time</span><Plus size={12} /><span>{num(dashboard.site.buffer_hours)}h buffer</span></div><span className="small-note">Based on the conservative reserve forecast.</span></section>
            </div>

            <div className="metric-row"><section className="metric-card"><span className="metric-icon"><Waves size={19} /></span><div><span className="metric-label">Time to reserve</span><strong>{num(a?.hours_to_reserve, true)} <small>hours</small></strong><p>Central projection · not physical empty time</p></div></section><section className="metric-card"><span className={`metric-icon ${a?.anomaly.active ? 'orange-icon' : ''}`}><Gauge size={19} /></span><div><span className="metric-label">Observed consumption</span><strong>{num(a?.current_rate_lph)} <small>L / hour</small></strong><p>{a?.anomaly.active ? <><ArrowUpRight size={12} />{num(a.anomaly.ratio, true)}× expected · abnormal depletion</> : <><CheckCircle2 size={12} />{num(a?.baseline_rate_lph)} L/h expected baseline</>}</p></div></section><section className="metric-card"><span className="metric-icon"><Truck size={19} /></span><div><span className="metric-label">Next planned supply</span><strong>{a?.next_supply_at ? time(a.next_supply_at) : 'Not planned'}</strong><p>{a?.next_supply_at ? `${date(a.next_supply_at)} · ${title(a.supply_status)}` : 'A planned arrival is not water in the tank.'}</p></div></section></div>

            <div className="middle-grid"><section className="card forecast-card"><div className="card-heading"><div><h3>Look ahead, act in time.</h3><p className="muted">Your storage outlook, with the reserve kept in view.</p></div><button className="button secondary small" onClick={() => { setModal('preview'); setPreview(null); }} disabled={isBusy}><SlidersHorizontal size={14} />What if?</button></div><ProjectionChart dashboard={dashboard} /><div className="chart-footnote"><Info size={13} /><span>{a?.uncertainty_label}</span></div></section>
              <section className={`card recommendation-card ${a?.anomaly.active ? 'attention' : ''}`}><div className="card-heading"><span className="eyebrow">YOUR NEXT MOVE</span><span className="recommendation-icon">{a?.anomaly.active ? <AlertTriangle size={18} /> : <ShieldCheck size={18} />}</span></div><h3>{a?.recommendation.title}</h3><p>{a?.recommendation.body}</p><div className="recommendation-fact"><span>Conservative reserve breach</span><strong>{a?.conservative_breach_at ? `${date(a.conservative_breach_at)} · ${time(a.conservative_breach_at)}` : 'No crossing available'}</strong></div><button className="button primary full" onClick={propose} disabled={isBusy || risk === 'UNKNOWN'}>{busy === 'Preparing request' ? 'Preparing request…' : 'Review supply request'}<ArrowRight size={16} /></button><small>Explicit approval required. Local demo notification only.</small></section>
            </div>

            <section className="scenario-lab"><div className="scenario-intro"><span className="lab-symbol"><FlaskConical size={22} /></span><div><h3>See the decision change.</h3><p>Run a simulated scenario through the actual reading workflow.</p></div></div><div className="scenario-buttons"><button className="button scenario excess" disabled={isBusy} onClick={() => changeScenario('excess_usage')}><ArrowDownRight size={16} />Excess usage</button><button className="button scenario" disabled={isBusy || (!activeIncident && !a?.anomaly.active)} onClick={() => changeScenario('repair')}><Wrench size={15} />Repair + readings</button><button className="button scenario" disabled={isBusy} onClick={() => changeScenario('delivery')}><Truck size={16} />Demo refill</button><button className="icon-button" title="Reset the isolated demo" aria-label="Reset demo" disabled={isBusy} onClick={() => setModal('reset')}><RefreshCw size={16} /></button></div></section>

            <div className="bottom-grid"><section className="card incident-card"><div className="card-heading"><div><h3>A clear trail from risk to recovery.</h3><p className="muted">{dashboard.incident ? `${title(dashboard.incident.status)} · ${dashboard.incident.reason}` : 'No active incident. Start a scenario to explore the response.'}</p></div><button className="text-button" onClick={() => setView('activity')}>View history<ArrowUpRight size={14} /></button></div><IncidentProgress dashboard={dashboard} />{lastAction && <div className="receipt-strip"><Send size={15} /><div><strong>{title(lastAction.status)}</strong><span>{lastAction.destination} · A receipt is not physical intervention.</span></div></div>}<Timeline dashboard={dashboard} compact /></section>
              <section className="card assistant-card"><div className="card-heading"><div className="assistant-title"><span className="assistant-avatar"><Droplets size={18} /></span><div><h3>Make sense of the signals.</h3><span className="tiny-label">Deterministic evidence guide</span></div></div></div><p className="muted">Answers use computed facts from this demo. No language model is involved.</p><div className="question-buttons"><button disabled={isBusy} onClick={() => ask('deadline')}>Why is this the action deadline?<ArrowRight size={14} /></button><button disabled={isBusy} onClick={() => ask('delay')}>What if supply is six hours late?<ArrowRight size={14} /></button><button disabled={isBusy} onClick={() => ask('buffer')}>What would give us more buffer?<ArrowRight size={14} /></button></div>{answer && <div className="assistant-answer" role="status"><span className="eyebrow">{answerVersion === dashboard.version ? 'CURRENT EVIDENCE' : 'EARLIER EVIDENCE · REFRESH THE ANSWER'}</span><p>{answer.answer}</p><small>Simulated · {title(answer.provider)} · version {answerVersion}</small></div>}<div className="assistant-footer"><ShieldCheck size={13} />Explains evidence. Cannot approve or resolve.</div></section></div>

            <div className="understated-actions"><span><Database size={13} />Observed state, stored locally. No live cloud deployment claimed.</span><button className="text-button" disabled={isBusy} onClick={() => { const rate = dashboard.analysis.current_rate_lph ?? dashboard.analysis.baseline_rate_lph; setVolume(rate == null ? '' : String(Math.round(Math.max(0, dashboard.state.volume_l - rate * 0.5)))); setModal('reading'); }}><Plus size={14} />Add a demo reading</button><button className="text-button" onClick={() => setView('evidence')}>Inspect evaluation<ArrowUpRight size={14} /></button></div>
          </>}
        <footer className="page-footer"><span><Droplets size={13} />JalRakshak · Care for every drop.</span><span>Evidence before reassurance.</span></footer>
      </main>
    </div>

    {isBusy && dashboard && <div className="busy-indicator" role="status"><RefreshCw size={14} className="spin" />{busy}…</div>}
    {modal === 'preview' && dashboard && <Dialog title="A plan with a little more foresight." close={() => setModal(null)} wide><p className="dialog-description">Preview a delayed planned delivery without changing observations or the incident. Unconfirmed supply does not extend the conservative action deadline.</p><label className="range-label" htmlFor="delay">Planned supply delay<span>{delayHours} hours</span></label><input id="delay" type="range" min="0" max="24" step="1" value={delayHours} onChange={event => { setDelayHours(Number(event.target.value)); setPreview(null); }} /><div className="range-extents"><span>On schedule</span><span>24 hours late</span></div><button className="button primary" disabled={isBusy} onClick={runPreview}>{busy === 'Computing preview' ? 'Computing…' : 'Compare this plan'}<ArrowRight size={15} /></button>{modalError && <p className="inline-error" role="alert">{error}</p>}{preview && <div className="preview-result"><Badge tone="neutral">Simulated · preview only</Badge><p>{preview.summary}</p><div className="preview-metrics"><div><span>Central reserve breach</span><strong>{preview.analysis.reserve_breach_at ? `${date(preview.analysis.reserve_breach_at)} · ${time(preview.analysis.reserve_breach_at)}` : 'No crossing in horizon'}</strong></div><div><span>Projected shortage duration</span><strong>{num(preview.analysis.shortage_hours, true)} hours</strong></div><div><span>Unmet demand</span><strong>{num(preview.analysis.unmet_demand_l)} L</strong></div></div><ProjectionChart dashboard={dashboard} analysis={preview.analysis} /><p className="small-note">The comparison uses the same observed state. A preview cannot book water or verify recovery.</p></div>}</Dialog>}
    {approval && dashboard && <Dialog title="Review the exact supply request." close={() => { if (!isBusy) setApproval(null); }}><Badge tone="neutral">Local simulated notification</Badge><p className="dialog-description">Approve this specific request using its current evidence. The local prototype records a demo receipt; it does not send to a supplier or book a tanker.</p><dl className="approval-details"><div><dt>Action</dt><dd>{title(approval.type)}</dd></div><div><dt>Destination</dt><dd>{approval.destination}</dd></div><div><dt>Evidence version</dt><dd>{approval.evidence_version}</dd></div><div><dt>Message</dt><dd>{approval.message}</dd></div></dl><label className="confirmation"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I approve this exact simulated request and its listed destination.</span></label>{modalError && <p className="inline-error" role="alert">{error}</p>}<div className="dialog-actions"><button className="button secondary" disabled={isBusy} onClick={() => setApproval(null)}>Cancel</button><button className="button primary" disabled={!confirmed || isBusy} onClick={approve}>{busy === 'Recording approval' ? 'Recording…' : 'Approve demo request'}<Check size={16} /></button></div></Dialog>}
    {modal === 'reading' && dashboard && <Dialog title="Add an observation to the demo tank." close={() => setModal(null)}><p className="dialog-description">This simulated entry advances the demo clock by 30 minutes. The suggested volume uses the current computed consumption rate; you can change it. It does not represent a real tank reading.</p><form onSubmit={submitReading}><label className="form-label" htmlFor="volume">Next simulated volume in litres</label><div className="unit-input"><input id="volume" type="number" required min="0" max={dashboard.site.capacity_l} step="1" value={volume} onChange={event => setVolume(event.target.value)} /><span>L</span></div><p className="small-note">Capacity: {num(dashboard.site.capacity_l)} L · Next observation: {date(new Date(new Date(dashboard.clock).getTime() + 30 * 60000).toISOString())}, {time(new Date(new Date(dashboard.clock).getTime() + 30 * 60000).toISOString())} IST</p>{modalError && <p className="inline-error" role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="button secondary" disabled={isBusy} onClick={() => setModal(null)}>Cancel</button><button className="button primary" type="submit" disabled={isBusy || volume.trim() === ''}>{busy === 'Saving demo reading' ? 'Saving…' : 'Save demo reading'}<Plus size={15} /></button></div></form></Dialog>}
    {modal === 'reset' && <Dialog title="Start with a fresh demo." close={() => setModal(null)}><p className="dialog-description">Reset this isolated session's simulated readings, incident, requests and event history. No real observations or external notifications are involved.</p>{modalError && <p className="inline-error" role="alert">{error}</p>}<div className="dialog-actions"><button className="button secondary" disabled={isBusy} onClick={() => setModal(null)}>Keep current demo</button><button className="button primary" disabled={isBusy} onClick={() => void perform('Resetting demo', async () => { setDashboard(await request<Dashboard>('/demo/reset', {})); setAnswer(null); setApproval(null); setModal(null); setNotice('A fresh isolated demo is ready.'); })}>Reset demo<RefreshCw size={15} /></button></div></Dialog>}
  </div>;
}

function ActionRecords({ dashboard }: { dashboard: Dashboard }) {
  return <section className="card"><div className="card-heading"><h3>Requests and notification evidence</h3><Send size={18} /></div>{dashboard.actions.length ? <div className="action-records">{[...dashboard.actions].reverse().map(action => <div className="action-record" key={action.id}><div><strong>{title(action.type)}</strong><p>{action.message}</p><small>{action.destination} · Evidence version {action.evidence_version}</small></div><Badge tone={action.status === 'FAILED' ? 'orange' : 'neutral'}>{title(action.status)}</Badge></div>)}</div> : <div className="empty-state"><Send size={25} /><p>No requests yet. Review a supply request from Overview.</p></div>}<p className="small-note">Publication and local receipt prove message handling, not human acknowledgment, supply arrival or physical repair.</p></section>;
}
