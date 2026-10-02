# Prompt 09 — Optional evidence-grounded Strands assistant

**Gate:** complete core loop and available time. **Result:** useful explanation/what-if assistance, never numerical authority.

```text
Read AGENTS.md, docs/PROJECT_STATE.md, evidence, and demo plan. If core
or reliability gates are incomplete, skip this optional milestone and
explain which core gate receives the time. Don't add an assistant to hide
missing deterministic behavior.

Verify current official Strands documentation and installable version.
Use a supported provider only if actual account credentials/model access
are available. Codex/Plus access is not an application API or Bedrock key.
Never hard-code a model ID, region entitlement, or promised free access.

Add bounded read/simulation tools: get_state, get_forecast, get_incident,
simulate_supply_delay, simulate_demand_change, simulate_added_supply.
Scope tools to the current authorized site and evidence version. Simulations
return a preview without writing readings, proposals, approvals, or actions.
Do not expose approval/notification/resolve tools to the agent. Do not
give it shell, filesystem, arbitrary URL, or unrestricted cloud tools.

Return structured fact references and short explanations. Bind each
operational claim to a tool field, unit, timestamp and provenance. A
number-whitelist alone is insufficient: the same number can be assigned
the wrong meaning/unit/time. Prefer backend-rendered numeric facts plus
model text that cites fact IDs. Reject unsupported/stale claims and use
a deterministic template on validation/provider/timeout failure.

Suggested questions: Why did the deadline move? What if supply is six
hours late? How much buffer would an extra delivery create? Keep the
assistant as a small panel, not the whole product.

Test tool schema/range bounds, wrong-site access, invented/wrong-unit facts,
stale evidence, malicious instructions in data, missing data, provider
failure, and attempts to approve or resolve. Fake-model tests are not proof
of live inference. Record a real call/tool trace if available, and label
scripted tests or deterministic fallback visibly. Run relevant checks;
update state/evidence/limitations; commit. Next Prompt 10.
```
