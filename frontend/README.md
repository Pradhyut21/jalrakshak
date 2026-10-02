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

The UI discloses simulated history, local notification receipts and a
deterministic evidence guide. It does not claim live sensors, supplier
bookings, a language model or cloud deployment. Manual entries are
`manual_demo` observations with `simulated: true`; the form explicitly advances
the isolated demo clock by 30 minutes using the API's bounded `advance_clock`
path. The optional volume suggestion is derived from the current API rate and
is disclosed as simulated. All mutations await the
actual API result before updating state. Error responses preserve the last
known dashboard, while previews and earlier assistant evidence are marked.

React, React DOM, Vite, TypeScript and Lucide are standard licensed
dependencies. Exact versions are captured in `package-lock.json`; preserve
the dependency license notices when redistributing bundled builds.
