# Third-party notices and observed dependency inventory

Audited 2 October 2026 from the application's actual Windows `.venv` and `frontend/node_modules`. This is the implementation inventory; older `prep/` license records describe earlier research and proposed tools.

The [machine-readable inventory](artifacts/dependency-licenses.json) records exact installed versions, requirement/lock agreement, direct and transitive roles, metadata, source URLs, observed license-file paths and SHA-256 hashes. It contains **35 Python distributions and 25 installed npm packages**. Another **44 npm lock entries were not installed on this host** and are listed separately, without a claim that their license texts were inspected. No declared direct dependency is missing, and observed installed versions match the current requirement/lock records.

## Direct application dependencies

| Component | Installed version | Observed license evidence |
|---|---|---|
| FastAPI | 0.142.2 | MIT metadata and license text |
| Uvicorn | 0.54.0 | BSD-3-Clause metadata and license text |
| Pydantic | 2.13.5 | MIT metadata and license text |
| HTTPX | 0.28.1 | BSD-3-Clause metadata and license text |
| Boto3 | 1.43.106 | Apache-2.0 metadata, license and NOTICE |
| Mangum | 0.22.0 | MIT classifier and license text |
| React / React DOM | 19.3.0 / 19.3.0 | MIT metadata and license text |
| Lucide React | 1.49.0 | ISC metadata; complete license also preserves MIT attribution for listed Feather-derived icons |

Complete observed direct-dependency texts are preserved verbatim under [docs/licenses](docs/licenses/INDEX.md). Their copyright notices and license conditions remain those of the respective upstream owners. The application's original-code license does not replace these notices.

## Development and validation tools

| Component | Installed version | Observed license evidence |
|---|---|---|
| pytest | 9.1.1 | MIT |
| Playwright Python | 1.63.0 | Apache-2.0 plus the installed driver and bundled third-party notices |
| PyYAML | 6.0.3 | MIT; development and offline infrastructure validation |
| TypeScript | 7.0.2 | Apache-2.0 license and NOTICE |
| Vite | 8.3.2 | MIT metadata; complete supplied license includes bundled-component notices |
| Vite React plugin | 6.1.1 | MIT |
| React / React DOM type definitions | 19.3.0 / 19.3.0 | MIT |

The inventory separately records observed transitive packages, including Certifi's MPL-2.0 metadata and supplied license text. Transitive file hashes and paths are recorded; their full texts are not all copied into this source archive. Installed dependencies retain their own distributed notices.

## Evidence gaps and scope

The optional development package `@rolldown/binding-win32-x64-msvc` **1.2.12** declares MIT in its installed `package.json`, but no package-root license/notice text was observed. Its evidence status is `METADATA_ONLY`; it is not silently treated as text-audited.

This audit reads installed metadata and license/notice files. It is not a legal opinion, security assessment, exhaustive embedded-asset review, or inventory of separately downloaded browser binaries. The Windows installation does not establish the dependencies of a future Linux Lambda build. Repeat the inventory and inspect the actual deployment/distribution artifacts after dependency or platform changes. Preserve required notices when shipping compiled bundles or dependency binaries.

## Research and AI assistance

Beacon, CampusEvac and Fraud Risk Manager were inspected as private research references; their source is not copied into this application or shared source package. WNTR and EPANET are domain references, not installed application dependencies. Strands Agents SDK, OpenAI API calls and Bedrock model calls are not used in the current implementation. SAM YAML describes infrastructure; it does not bundle the SAM CLI.

The current UI source has no observed remote image or font imports; it uses application SVG/layout and the licensed Lucide icon dependency. This observation is limited to the inspected source tree.

Codex assisted research, original implementation, tests, document writing and artifact verification. The final submission must disclose the actual assistance and reused dependencies and preserve the true pre-event implementation dates.

To regenerate the installed-package evidence, run from the extracted repository root using the application's Python environment:

```text
python scripts/license_inventory.py
```

Install `backend/requirements-dev.txt` as well as the runtime requirements before auditing this complete development inventory; the script uses `packaging` from that environment. Use the interpreter that runs the application, not an unrelated global Python.
