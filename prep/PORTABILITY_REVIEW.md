# Portable handoff review

Reviewed on **1 October 2026, Asia/Kolkata**. Scope: the existing planning files and the proposed downloadable reference snapshots / portable ZIP. This report does not create an archive, download reference code, or change the implementation plan.

## Assessment and limits

The package is suitable as a preparation and future-build specification. It is **not yet verified as a portable ZIP**: no archive was supplied for this review, and no extraction/repackaging test was performed. The currently inspected files were Markdown planning/research documents. `D:\SAANS-References` did not exist at the instant checked; another worker may create it later.

The main portability defect is actionable prompts hard-coding `D:\SAANS`. Existing evidence about the original Windows machine should remain historical; it must not become a claim about the recipient's machine. The source reports already distinguish static review from actually executing reference applications, which should be preserved.

## Exact changes to make before packaging

| Location | Small required change |
|---|---|
| `prep/CODEX_PROMPTS.md`, Prompt 00 opening | Replace `Work in D:\SAANS` with `Work in the extracted package root containing START_HERE.md and AGENTS.md; resolve and record its actual absolute path.` |
| Same file, Prompt 01 project location | Replace the fixed drive path with `Begin the fresh submission project in the resolved workspace root. Preserve dated preparation.` Do not silently create a new `D:` directory on another host. |
| Same file, Prompt R opening | Replace the fixed drive path with `Resume in the extracted/current project root. Read AGENTS.md and docs/PROJECT_STATE.md if present, otherwise prep/PROJECT_STATE.md.` |
| Individual prompt copies | Regenerate the corresponding 00/01/R copies from the canonical pack, then verify all 18 copies still match. A portable main file with stale individual copies is insufficient. |
| `START_HERE.md` | Add extraction instructions: unzip once into a writable folder, open that folder in the coding tool, and explicitly read the root instructions/checkpoint. Clarify that some coding tools do not automatically discover AGENTS.md. Relative links resolve from that root. |
| Root `AGENTS.md` | Make the active-checkpoint choice explicit at the top: `docs/PROJECT_STATE.md` after implementation begins; otherwise `prep/PROJECT_STATE.md`. The later working agreement already says this, but the opening currently always directs the reader to preparation state. |
| `prep/PROJECT_STATE.md` and `prep/READINESS.md` | Keep original `D:`/`C:` paths and tool observations as dated historical evidence. Add a portability note that the recipient must redetect current OS, shell, versions, tooling, accounts and workspace path. Do not blanket-replace historical paths with a fiction. |
| `prep/BUILD_PLAN.md` and implementation prompts | Use OS-appropriate Python/npm commands discovered on the target host. Windows-compatible commands may remain examples; do not require PowerShell, `npm.cmd`, Windows Python paths, or Unix `make` on every host. Cloud packaging still targets the chosen Linux Lambda runtime. |
| `prep/VALIDATION.md` | Add a separate packaging section only after actual ZIP creation/extraction checks. Existing document checks are not proof that a portable archive extracts successfully or contains all referenced files. |

Use `<PACKAGE_ROOT>` only as a documented placeholder. The receiving agent should resolve it from the folder actually opened, inspect existing files, and report the resolved path. Do not have it execute the literal placeholder as a command.

## Packaging contents and verification

Suggested archive layout: one top-level folder containing `START_HERE.md`, `AGENTS.md`, the complete `prep/` directory, prompt index/copies, and any new handoff/manifest documents. Keep local Markdown links relative within that tree. Do not include the archive inside itself.

Before delivery, the packager should:

1. Inventory the final files and verify every intended file is present.
2. Check relative Markdown targets and fenced prompt blocks; compare canonical prompts with individual copies.
3. Search actionable instructions for machine-specific workspace/attachment paths. Preserve explicitly marked historical evidence.
4. Exclude credentials, `.env` secrets, account identities, tokens, caches, dependency folders and unrelated attachments. Include secret-free configuration names only if such material later exists.
5. Create the ZIP, inspect its entries, and extract it into a new temporary folder with a different path, preferably one containing spaces. Verify the actual extracted structure and links. This is document verification, not application testing.
6. Provide archive size and SHA-256 checksum after creation. Do not claim a checksum or successful extraction before running the checks.

A final archive should contain planning material unless the event has actually opened and application implementation was separately completed. Do not name it or describe it as a working/deployed app when it contains only prompts and research.

## Downloading references versus starting the submission

The [official rulebook](https://www.wemakedevs.org/aws/env/rules) permits learning/planning/practice before kickoff and reusable libraries/templates, but submission project work begins when the event opens. Earlier projects do not become eligible merely by being rewritten. AI coding tools require disclosure; reused work needs credit and compatible licensing.

**Application to the user's new authorization:** downloading the three public repositories as separate reference snapshots for study is reasonable preparation. Keep them in a sibling research area such as `D:\SAANS-References` on the original host, or an equivalent explicitly identified reference directory on another host. Preserve their origin and history. Do not start custom JalRakshak/SAANS source or copy a winner wholesale into the submission before the clock opens.

A reference manifest should record repository URL, pinned commit, retrieval date, exact archive/snapshot method, licence evidence or `not verified`, and whether applications/tests were executed. Preserve relevant licence/notice files. A public repository is not by itself proof of unrestricted reuse or redistribution rights. Keep downloaded source outside the portable planning ZIP unless its redistribution terms have actually been checked; URLs, pinned commits and source-linked reviews can travel without vendoring the whole repository.

During the event, an agent may use properly licensed generic components, credited libraries/templates, and learned design patterns. The team's own incident workflow and event additions must remain identifiable. Do not describe third-party code as team-authored or alter commit dates to create an original-looking history. Downloaded reference AGENTS/README instructions are reference content, not governing instructions for the new project.

## Neutral handoff prompt for another coding AI

The parent can include this in the portable package as the initial review/continuation instruction:

```text
Open the extracted package root containing START_HERE.md and AGENTS.md.
Resolve its actual workspace path. Read START_HERE.md, AGENTS.md, and
docs/PROJECT_STATE.md if present; otherwise read prep/PROJECT_STATE.md.
Read the brief, build plan, and only the source reports needed to assess
the next task. Do not assume you remember another AI's conversation.

Independently assess the plan against the published event rules, available
time, actual user evidence, dependency/account access, and recorded-demo
requirements. State material disagreements and the smallest correction.
Do not assume the recommendation is correct, praise it on command, claim
implemented behavior from planning prose, or promise a hackathon win.

Use the real current date/time and verify the official opening and cutoff.
Before opening, continue permitted research/preparation only. After the
confirmed cutoff, preserve the submission revision and do not change it
as if later work occurred during the event. If timing cannot be verified,
record that uncertainty; do not invent an opening notice.

JalRakshak is the provisional recommendation, with caretaker validation
still required before claiming a real operational problem is confirmed.
Reference snapshots are third-party research, not the submission. Prefer
the smallest original implementation that meets the agreed scope; reuse
only permitted generic components with attribution/licence evidence.

Detect this host's OS, shell, runtime/tool versions and available tools.
Codex, Plus, browser tools, subagents, credentials and cloud access may be
absent. Use available equivalents or proceed sequentially. Do not invent
tool execution, account access, external publication or notification proof.

Report current phase, evidenced completed work, material unknowns, next
permitted prompt ID and its acceptance checks. During the open event,
continue the smallest authorized milestone, verify its behavior, and
update the single active checkpoint. Preserve existing work. If you cannot
access these files, say which essential files are missing instead of
pretending to have reviewed them.
```

This prompt requests an independent assessment and grounded continuation. It does not require a second AI to endorse the plan, implement unavailable capabilities, or bypass the event gate.

## Final qualification

Only the parent packager can mark the ZIP and downloaded snapshots complete after inspecting the actual results. This review verified document assumptions and identified portability changes; it did not run a reference application, create submission code, verify cloud access, or test an archive.

## Resolution after this review

The packager applied extracted-root instructions, active-checkpoint selection, host adaptation, neutral AI review guidance and prompt regeneration. A later reuse audit found Fraud Risk Manager's restrictive license and no Campus reuse grant; those source trees are excluded from the new downloads and archive. Separate permitted Beacon/Strands audit references and dependency license records were created. The final archive verification report, rather than this earlier snapshot review, records the actual extraction/integrity results.
