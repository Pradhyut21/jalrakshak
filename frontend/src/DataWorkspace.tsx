import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Database, Download, FileUp, Info, Save, SlidersHorizontal, Truck } from 'lucide-react';
import { request } from './api';
import type { Dashboard } from './api';

export function localTimestamp(iso = new Date().toISOString()): string {
  return new Date(new Date(iso).getTime() + 330 * 60000).toISOString().slice(0, 16);
}
export function utcTimestamp(local: string): string {
  const parsed = new Date(`${local}+05:30`);
  if (!Number.isFinite(parsed.getTime())) throw new Error('Enter a valid observation time in IST.');
  return parsed.toISOString();
}
type ImportedReading = { reading_id: string; observed_at: string; volume_l: number; source: 'manual_observed'; simulated: false };
type ImportedArrival = { id: string; arrived_at: string; amount_l: number };
type ImportData = { readings: ImportedReading[]; deliveries: ImportedArrival[] };

function csvRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++; }
      else if (quoted || field.length === 0) quoted = !quoted;
      else throw new Error('Unexpected quote in CSV. Use ordinary comma-separated columns.');
    } else if (char === ',' && !quoted) { row.push(field.trim()); field = ''; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i++;
      row.push(field.trim()); field = '';
      if (row.some(value => value.length > 0)) rows.push(row);
      row = [];
    } else field += char;
  }
  if (quoted) throw new Error('A quoted CSV field is not closed.');
  row.push(field.trim());
  if (row.some(value => value.length > 0)) rows.push(row);
  return rows;
}
function explicitTime(value: unknown, label: string): string {
  if (typeof value !== 'string' || !/(Z|[+-]\d{2}:\d{2})$/i.test(value) || !Number.isFinite(new Date(value).getTime())) throw new Error(`${label} needs an ISO timestamp with Z or a timezone offset, for example +05:30.`);
  return new Date(value).toISOString();
}
function parseLogs(csv: string, arrivals: string, capacity: number): ImportData {
  const rows = csvRows(csv.replace(/^\uFEFF/, ''));
  const readings: ImportedReading[] = [];
  if (rows.length) {
    const headers = rows[0].map(value => value.trim().toLowerCase());
    const timeIndex = headers.indexOf('observed_at'), volumeIndex = headers.indexOf('volume_l'), idIndex = headers.indexOf('reading_id');
    if (timeIndex < 0 || volumeIndex < 0) throw new Error('CSV requires observed_at and volume_l headers. reading_id is optional.');
    if (rows.length - 1 > 1000) throw new Error('Import at most 1,000 observations at a time.');
    rows.slice(1).forEach((row, i) => {
      if (row.length !== headers.length) throw new Error(`CSV row ${i + 2} has a different column count.`);
      const volume = row[volumeIndex] === '' ? NaN : Number(row[volumeIndex]);
      if (!Number.isFinite(volume) || volume < 0 || volume > capacity) throw new Error(`CSV row ${i + 2} volume must be between zero and the configured capacity.`);
      readings.push({ reading_id: idIndex >= 0 && row[idIndex] ? row[idIndex] : crypto.randomUUID(), observed_at: explicitTime(row[timeIndex], `CSV row ${i + 2}`), volume_l: volume, source: 'manual_observed', simulated: false });
    });
  }
  const deliveries: ImportedArrival[] = [];
  if (arrivals.trim()) {
    const parsed: unknown = JSON.parse(arrivals);
    if (!Array.isArray(parsed) || parsed.length > 100) throw new Error('Arrivals JSON must be an array with at most 100 recorded arrivals.');
    parsed.forEach((item: unknown, index: number) => {
      if (!item || typeof item !== 'object') throw new Error(`Arrival ${index + 1} is not an object.`);
      const value = item as Record<string, unknown>;
      if (typeof value.id !== 'string' || !value.id.trim()) throw new Error(`Arrival ${index + 1} requires a stable id.`);
      if (typeof value.amount_l !== 'number' || !Number.isFinite(value.amount_l) || value.amount_l <= 0) throw new Error(`Arrival ${index + 1} requires a positive amount_l.`);
      deliveries.push({ id: value.id, arrived_at: explicitTime(value.arrived_at, `Arrival ${index + 1}`), amount_l: value.amount_l });
    });
  }
  if (!readings.length && !deliveries.length) throw new Error('Add observations or recorded arrivals before importing.');
  return { readings, deliveries };
}

interface Props { dashboard: Dashboard; onDashboard: (value: Dashboard) => void; onBusy: (label: string) => void; busy: boolean }

export default function DataWorkspace({ dashboard, onDashboard, onBusy, busy }: Props) {
  const live = dashboard.mode === 'LOCAL_OBSERVED';
  const available = dashboard.features?.local_observed_mode === true;
  const [name, setName] = useState(dashboard.site.name);
  const [capacity, setCapacity] = useState(String(dashboard.site.capacity_l));
  const [reserve, setReserve] = useState(String(dashboard.site.reserve_l));
  const [lead, setLead] = useState(String(dashboard.site.lead_hours));
  const [buffer, setBuffer] = useState(String(dashboard.site.buffer_hours));
  const [measurement, setMeasurement] = useState(String(dashboard.site.measurement_error_l ?? 100));
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [csv, setCsv] = useState('');
  const [arrivals, setArrivals] = useState('');
  const [parsed, setParsed] = useState<ImportData | null>(null);
  const [arrivalType, setArrivalType] = useState<'arrived' | 'planned'>('arrived');
  const [amount, setAmount] = useState('');
  const [arrivalAt, setArrivalAt] = useState(localTimestamp());
  const [deliveryId, setDeliveryId] = useState<string>(crypto.randomUUID());
  useEffect(() => {
    setName(dashboard.site.name); setCapacity(String(dashboard.site.capacity_l)); setReserve(String(dashboard.site.reserve_l));
    setLead(String(dashboard.site.lead_hours)); setBuffer(String(dashboard.site.buffer_hours));
    setMeasurement(String(dashboard.site.measurement_error_l ?? 100)); setConfirmed(false);
  }, [dashboard.site.id, dashboard.mode]);
  const run = async (label: string, action: () => Promise<void>) => {
    setError(''); setNotice(''); onBusy(label);
    try { await action(); } catch (err) { setError(err instanceof Error ? err.message : 'The operation failed. Nothing is assumed saved.'); } finally { onBusy(''); }
  };
  const settings = () => ({ name: name.trim(), capacity_l: Number(capacity), reserve_l: Number(reserve), lead_hours: Number(lead), buffer_hours: Number(buffer), measurement_error_l: Number(measurement), time_zone: 'Asia/Kolkata' });
  const configure = (event: FormEvent) => {
    event.preventDefault();
    if (!live && !confirmed) return;
    void run(live ? 'Saving tank settings' : 'Opening observed workspace', async () => {
      const value = await request<Dashboard>(live ? '/site' : '/workspace/live', settings());
      onDashboard(value); setConfirmed(false); setParsed(null);
      setNotice(live ? 'Tank settings saved. Forecasts were recomputed from stored observations.' : 'The local observed workspace is empty. Enter actual logs; risk remains UNKNOWN until usable evidence exists.');
    });
  };
  const previewImport = () => {
    setError(''); setNotice('');
    try { setParsed(parseLogs(csv, arrivals, dashboard.site.capacity_l)); } catch (err) { setParsed(null); setError(err instanceof Error ? err.message : 'Unable to parse these logs.'); }
  };
  const importData = () => {
    if (!parsed) return;
    void run('Importing recorded logs', async () => {
      onDashboard(await request<Dashboard>('/import', parsed));
      setNotice('The complete import was accepted by the server. Recorded arrivals and observations retain operator-entered provenance.');
      setParsed(null); setCsv(''); setArrivals('');
    });
  };
  const recordDelivery = (event: FormEvent) => {
    event.preventDefault();
    void run(arrivalType === 'arrived' ? 'Recording arrival' : 'Recording supply plan', async () => {
      const timestamp = utcTimestamp(arrivalAt);
      const payload = { id: deliveryId, amount_l: Number(amount), ...(arrivalType === 'arrived' ? { arrived_at: timestamp } : { scheduled_at: timestamp }) };
      onDashboard(await request<Dashboard>('/deliveries', payload));
      setAmount(''); setDeliveryId(crypto.randomUUID());
      setNotice(arrivalType === 'arrived' ? 'Operator-entered arrival saved in the inflow ledger. Record the measured tank level separately; water is not counted twice.' : 'Planned supply saved. It is conditional and is not recorded as arrived water.');
    });
  };
  const exportBackup = () => void run('Preparing local backup', async () => {
    const backup = await request<Record<string, unknown>>('/export', {});
    const objectUrl = URL.createObjectURL(new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = objectUrl; anchor.download = `jalrakshak-local-backup-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(anchor); anchor.click(); anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    setNotice('A JSON backup was prepared for your browser to download. Keep it locally; it contains your operator-entered records.');
  });
  return <div className="data-workspace">
    {error && <div className="alert-banner error" role="alert"><AlertTriangle size={17} /><span>{error}</span></div>}
    {notice && <div className="alert-banner success" role="status"><CheckCircle2 size={17} /><span>{notice}</span></div>}
    <section className="card workspace-intro"><div className="card-heading"><div><span className="eyebrow">YOUR INPUTS, CLEARLY IDENTIFIED</span><h2>{live ? 'Local observations, not demo fixtures.' : 'Start from the tank you actually manage.'}</h2></div><Database size={23} /></div><p>{live ? 'This private local session stores operator-entered logs. The app does not certify their accuracy or imply connected sensors. Risk uses wall-clock freshness and recorded inflow.' : 'The demonstration stays separate from actual logs. On a local backend, you can replace this session with an empty observed workspace and enter your tank settings. Cloud guest deployments cannot open observed workspaces.'}</p></section>
    <section className="card"><div className="card-heading"><div><h3>{live ? 'Tank settings' : 'Configure a local observed workspace'}</h3><p className="muted">{live ? 'Change documented assumptions; historical readings remain intact.' : 'Replace the sample settings with actual tank parameters. This transition clears this session’s demo observations.'}</p></div><SlidersHorizontal size={19} /></div>
      {!available && <div className="data-info"><Info size={16} /><p>Observed workspaces are disabled on this deployment. Use the local application with private storage.</p></div>}
      <form onSubmit={configure}><div className="data-fields"><label className="data-field wide-field">Tank / site name<input required maxLength={100} value={name} onChange={event => setName(event.target.value)} /></label><label className="data-field">Capacity · litres<input type="number" required min="1" step="1" value={capacity} onChange={event => setCapacity(event.target.value)} /></label><label className="data-field">Unusable reserve · litres<input type="number" required min="0" max={Number(capacity) - 1} step="1" value={reserve} onChange={event => setReserve(event.target.value)} /></label><label className="data-field">Supply lead time · hours<input type="number" required min="0" max="48" step="0.5" value={lead} onChange={event => setLead(event.target.value)} /></label><label className="data-field">Planning buffer · hours<input type="number" required min="0" max="48" step="0.5" value={buffer} onChange={event => setBuffer(event.target.value)} /></label><label className="data-field">Reading error assumption · litres<input type="number" required min="0" max={Number(capacity)} step="1" value={measurement} onChange={event => setMeasurement(event.target.value)} /></label><div className="data-field timezone-field">Time zone<span>Asia/Kolkata · IST (UTC+05:30)</span></div></div>
        {!live && <label className="confirmation workspace-confirmation"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} /><span>I want to discard this session’s simulated observations and open an empty local workspace with these tank settings. I will enter actual observations rather than label demo data as real.</span></label>}
        <div className="data-form-actions"><span className="small-note">Supply lead time + planning buffer must total at most 48 hours, the forecast horizon. No shared public real-site data or production identity system is implied.</span><button className="button primary" disabled={busy || !available || (!live && !confirmed)} type="submit">{live ? 'Save tank settings' : 'Open empty observed workspace'}{live ? <Save size={16} /> : <ArrowRight size={16} />}</button></div>
      </form>
    </section>
    {live && <>
      <section className="card backup-card"><div><h3>Keep a copy of your local evidence.</h3><p>This local session retains records for 30 days without a write and keeps at most the newest 1,000 observations and 200 supply records. Export backups before records expire or exceed these limits. A backup contains your entered logs, settings and action history; it excludes session cookies and CSRF tokens.</p></div><button className="button secondary" disabled={busy} onClick={exportBackup}><Download size={16} />Download JSON backup</button></section>
      <section className="card"><div className="card-heading"><div><h3>Import recorded tank logs</h3><p className="muted">Preview first. The server validates all records and saves the import atomically.</p></div><FileUp size={21} /></div>
        <div className="data-info"><Info size={16} /><p>Use ISO timestamps with a timezone. CSV columns: <code>reading_id</code> (optional), <code>observed_at</code>, <code>volume_l</code>. All records are operator-entered, not authenticated sensor telemetry. Maximum 1,000 observations and 100 arrivals per import.</p></div>
        <div className="log-inputs"><div className="data-field csv-column"><label className="data-field">Observations CSV<textarea aria-label="Observations CSV" rows={8} spellCheck={false} placeholder={'reading_id,observed_at,volume_l\nPaste your actual tank logs here.'} value={csv} onChange={event => { setCsv(event.target.value); setParsed(null); }} /></label><label className="data-field file-upload-field">Or choose a CSV file<input className="file-input" type="file" accept=".csv,text/csv" aria-label="Choose observations CSV" onChange={event => { const file = event.target.files?.[0]; if (!file) return; if (file.size > 2000000) { setError('Use a CSV smaller than 2 MB.'); return; } void file.text().then(text => { setCsv(text); setParsed(null); }).catch(() => setError('Unable to read the selected CSV.')); }} /></label></div><label className="data-field">Optional recorded arrivals · JSON array<textarea aria-label="Optional recorded arrivals · JSON array" rows={8} spellCheck={false} placeholder={'[{"id":"your-stable-id","arrived_at":"ISO timestamp with timezone","amount_l":...}]'} value={arrivals} onChange={event => { setArrivals(event.target.value); setParsed(null); }} /><span className="small-note">Only enter water that actually arrived. Keep pending deliveries as plans below.</span></label></div>
        {parsed && <div className="import-preview" role="status"><CheckCircle2 size={17} /><div><strong>{parsed.readings.length} observations · {parsed.deliveries.length} recorded arrivals ready to submit</strong><p>Parsed locally; not saved yet. Duplicate IDs and conflicting timestamps are checked by the server.</p></div></div>}
        <div className="data-form-actions"><button className="button secondary" disabled={busy} onClick={previewImport}>Preview logs</button><button className="button primary" disabled={busy || !parsed} onClick={importData}>Import these records<FileUp size={16} /></button></div>
      </section>
      <section className="card"><div className="card-heading"><div><h3>Record supply separately from tank level</h3><p className="muted">An arrival is inflow evidence; it does not automatically increase a measured observation.</p></div><Truck size={21} /></div><form onSubmit={recordDelivery}><div className="data-fields"><label className="data-field">Supply record type<select value={arrivalType} onChange={event => setArrivalType(event.target.value as 'arrived' | 'planned')}><option value="arrived">Water actually arrived</option><option value="planned">Planned supply only</option></select></label><label className="data-field">{arrivalType === 'arrived' ? 'Arrival time' : 'Scheduled time'} · IST<input type="datetime-local" required value={arrivalAt} max={arrivalType === 'arrived' ? localTimestamp() : undefined} onChange={event => setArrivalAt(event.target.value)} /></label><label className="data-field">Volume · litres<input type="number" required min="1" step="1" value={amount} onChange={event => setAmount(event.target.value)} /></label><label className="data-field">Stable record ID<input required maxLength={100} value={deliveryId} onChange={event => setDeliveryId(event.target.value)} /></label></div><div className="data-form-actions"><span className="small-note">Operator-entered provenance. A plan is not an arrival or a supplier booking.</span><button type="submit" className="button primary" disabled={busy}>{arrivalType === 'arrived' ? 'Save recorded arrival' : 'Save supply plan'}<Save size={16} /></button></div></form></section>
    </>}
  </div>;
}
