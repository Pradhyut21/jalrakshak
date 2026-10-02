# Prompt P — Coordinate bounded parallel work

**Gate:** stable contract and disjoint file ownership.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, agreed contracts and BUILD_PLAN.
Identify genuinely independent subtasks in the current milestone. Use
available subagents if they improve speed or review quality; don't create
user-owned chats unless the user explicitly requests them.

You are the integrator. Own contract changes, migrations, dependency locks,
CI, deployment, and the shared checkpoint. Give each worker a bounded goal,
directory/file ownership, inputs, acceptance checks and handoff format.
Examples: forecast module/tests; frontend against stable API; read-only
review/evidence. No two workers edit the same file. Contract/dependency
changes return to you before integration. Shared filesystem means shared
edits; don't assume isolation. Separate human chats need worktrees or
explicit disjoint ownership.

Workers report owned files, behavior, exact checks/results, interface
expectations and unresolved failures. Don't let all workers update the
same state document or commit overlapping changes. Gather reports, inspect
diffs, resolve conflicts, integrate the actual workflow, and run the
relevant combined checks. If agents aren't available, execute sequentially.

Write one truthful checkpoint and commit scoped integrated work. Parallel
completion claims do not replace integration evidence. End with the next
incomplete gate, not a list of unconnected new feature ideas.
```
