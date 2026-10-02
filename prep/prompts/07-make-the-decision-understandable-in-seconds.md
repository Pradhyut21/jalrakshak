# Prompt 07 — Make the decision understandable in seconds

**Result:** a coherent operations screen with observable state changes.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, the current contract, and demo
outline. Improve the existing frontend around the functioning core.
Do not add backend domains, new models, or a decorative marketing site.

Design one operations screen for a caretaker. Lead with the reserve risk
and latest action time, then usable litres, reserve threshold, supply
status, data age/source, sensitivity range, and one recommended action.
Show the tank and storage trajectory, reserve line, planned supply marker,
and action deadline. Use simple chart/SVG components and the established
design system; unnecessary 3D is out of scope.

Keep a visible simulated/manual/modeled provenance badge. Distinguish
UNKNOWN, WATCH, ACT NOW and verified recovery through text/icons as well
as color. Display uncertain/overdue forecasts honestly. Explain reserve
versus empty time. A published notification cannot look like a completed
repair. Place Demo Lab controls apart from operational actions.

Make approval review the exact current proposal and destination scope.
Use accessible buttons, keyboard focus, readable contrast, and sensible
small-screen layout. Include loading, API unavailable, stale data, empty,
and retry states. Don't render invented zeroes while data loads. Keep
advanced evidence/metrics in a details drawer rather than many dashboards.

When browser tools are available, run the actual app and inspect the
main screen, abnormal scenario, pending verification, error state, and
a narrow viewport. Fix observed usability issues. If browser verification
is unavailable, state that limitation and supply a concrete manual check.

Run frontend typecheck/build and meaningful workflow/component checks.
Update the demo click path, evidence, and checkpoint. Commit. Next 08.
```
