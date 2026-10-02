# JalRakshak interface

Original React + TypeScript interface with Vite. Uses server-computed state;
there are no fallback fabricated readings, metrics, or successful actions.

From this directory, with Node 22.12 or newer:

```powershell
npm ci
npm run dev
```

Start the API using the repository's backend instructions. The Vite development
server runs on `http://127.0.0.1:5173` and proxies `/api` to
`http://127.0.0.1:8000`. `npm run preview` uses the same proxy on port 4173.

```powershell
npm run typecheck
npm run build
```

For separate hosting, the optional `VITE_API_BASE_URL` is the exact API origin
without a trailing `/api` (for example `https://api.example.com`). Configure it
at build time and configure the API's allowed origin and secure cookie policy.
The default is same-origin. Requests include session cookies; each mutation
uses the session-bound CSRF token returned by `GET /api/dashboard`.

The UI separates `SIMULATED_DEMO` from the local-only `LOCAL_OBSERVED`
workspace. Demo entries are `manual_demo`, `simulated: true`, and explicitly
advance the demo clock by 30 minutes. Their optional volume suggestion uses
the API's observed demand rate.

When `features.local_observed_mode` is true, Data & settings can open an empty
observed workspace after an unchecked confirmation. This discards that
session's demo observations. Tank settings, timestamped manual observations,
CSV logs and actual/planned supply records use the local API. Actual entries
are `manual_observed`, `simulated: false`: operator-entered and unverified,
with no inferred current volume. CSV requires `observed_at` and `volume_l`;
`reading_id` is optional. Timestamps must carry a timezone. Imports are
previewed locally and saved atomically by the server. A JSON backup download
includes stored evidence and settings, excluding session credentials.

Dashboard refresh runs every 30 seconds and when the page becomes visible;
the API owns wall-clock freshness. All mutations await the actual API result.
Errors preserve the last known dashboard. An automatic refresh failure is
visible, and changed evidence invalidates a prior what-if preview.

Forecast details disclose historical coverage, reading-error assumptions and
an empirical planning envelope. The envelope is not a calibrated probability
or guarantee. Synthetic reserve-timing results are shown separately from the
legacy demand benchmark. Notifications remain local receipts. The evidence
guide is deterministic; the UI claims no connected sensors, supplier bookings,
language model or completed cloud deployment.

React, React DOM, Vite, TypeScript and Lucide are standard licensed
dependencies. Exact versions are captured in `package-lock.json`; preserve
the dependency license notices when redistributing bundled builds.
