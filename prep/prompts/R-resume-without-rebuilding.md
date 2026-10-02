# Prompt R — Resume without rebuilding

**When:** a chat closes, context compacts, or you move to a new session.

```text
Resume the Environmental Hacks work in the current/extracted project root. Read AGENTS.md and
docs/PROJECT_STATE.md if present, otherwise prep/PROJECT_STATE.md.
Inspect Git status, recent commits, current files, and available evidence.
Don't assume earlier chat memory or a green gate from prose alone.

Identify the current milestone, what's implemented, dirty work ownership,
actual last check results, blockers, and the next incomplete acceptance
criterion. Read only the brief/code/docs needed for that next action.
Verify the current event window before code work. If not open, remain in
preparation; after the confirmed cutoff, preserve the submitted revision
and label any further development separately from the event submission.

Preserve completed work and other workers' edits. Do not scaffold again,
rename the project, replace the stack, retrain to obtain nicer metrics,
or repeat successful broad checks without a concrete reason. Repair stale
checkpoint statements from observed evidence and note any discrepancy.

Continue the smallest next action in the active milestone, run its relevant
checks, fix failures, and update the checkpoint. Report observed progress,
exact results, and the next prompt ID. Do not ask me to paste the old chat.
```
