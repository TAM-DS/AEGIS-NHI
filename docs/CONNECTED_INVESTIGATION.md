# Connected investigation | Shadow AI reference

**One working synthetic investigation, not a deployed cyber platform.** The new
Connected Investigation tab combines the existing shadow-AI case graph with a
version-bound fictional session/host fixture. No live telemetry, Palantir product
or other AEGIS repository is connected.

## Reproduce

```bash
uv sync --extra dev --extra dashboard
uv run pytest -q tests/test_connected_investigation.py tests/test_connected_ui.py
uv run streamlit run streamlit_app.py
```

Open **Connected Investigation** and select **SHADOW-003**. The registered agent's
request has a scoped grant, but uses an unregistered tool. Policy authorization,
tool-inventory findings and recorded execution are separate facts. An authorized
request does not prove every other policy was satisfied.

Expected fixture: four requests, two declared sessions, two host observations,
zero unassigned events, 29 graph nodes and 58 directed edges. These counts describe
this fixture only. Removing a session assignment leaves an event visibly unassigned;
the system does not infer the missing relationship from time or matching labels.

## Sources and adapter

- `data/scenarios/shadow_ai.json`: existing event, grant, tool registry, evidence
  and annual-loss assumptions. `adapt_case_events` normalizes its events into the
  bounded source contract and hashes the actual included evidence objects.
- `data/connected/shadow_sessions.json`: newly authored fictional session/host
  records, explicitly pinned to the case SHA-256, case ID and institution.
- The AEGIS Evidence companion fixture was inspected. It describes governance
  capabilities, not session/host event records; it was not repurposed as telemetry.

The adapter produces no implicit SAME_REPORTED_EVENT links. This projection adds
different relationship types with their own checks; it does not broaden the v1
cross-source same-event contract.

## Relationship rules

| Relationship | Required support |
|---|---|
| Identity → session | Exact identity of every assigned case event |
| Session → request | Explicit event ID, unique assignment, timestamp in [start, end) |
| Host observation → session | Explicit session reference and timestamp in its interval |
| Host observation → request | Event explicitly assigned to that same session |
| Session/host → evidence | Included fixture payload and its computed SHA-256 |
| Request → grant/resource/source evidence | Existing validated case-graph rules |

Unknown fields, wrong institution/case/revision, duplicate sessions or observations,
ambiguous assignments, invalid intervals and cross-session host references reject
the entire investigation. The supplemental source has a fixed identifier, at most
100 sessions and 100 host observations, and a 256 KiB serialized size ceiling.

The UI loads repository-owned fixtures only. It does not expose an arbitrary upload
or network ingestion endpoint. It shows a two-hop graph neighborhood for the chosen
request, raw evidence, policy decisions and a JSON download. Validation failures
show an error without displaying a partial connected report.

## Economics and authority

The case's **$0.019 fictional tool charges** are incident-window fixture costs.
Its annual exposure is the existing seeded conditional model using explicit
frequency and severity assumptions. The view labels both as whole-case context;
neither is a real bill or observed loss, and they must not be added together.

Every connected report remains NOT_AUTHORIZED_FOR_ACTION. The view can support a
human investigation recommendation; it cannot approve remediation. Hashes establish
consistency with the selected files, not source authenticity. Explicit references
do not establish causality or prove that a process performed a real action.

## Case-prep walkthrough

**Business objective:** help a bank analyst explain how a suspicious AI tool request
relates to identity, session, host evidence and policy, without overstating loss.

**Architecture decision:** use a deterministic, source-bound projection with explicit
relationship rules. Reuse the current policy replay and economics components.

**Trade-off:** strict schema and revision checks increase adapter maintenance and
reject incomplete data, but avoid silently turning plausible matches into findings.

**Failure demonstration:** change the telemetry case hash or assign a host to the
wrong session. The whole investigation fails validation. Restore the fixture and
show the same reproducible result.

**Business consequence:** the demonstration supports an evidence-quality discussion.
It does not yet demonstrate reduced analyst time, detection effectiveness or ROI.
Measure those in a separately authorized pilot against an agreed baseline.

**Next decision:** choose one genuine source schema and its accountable owner,
authenticate provenance, and validate mapping accuracy before introducing a live feed.
External-source adapters, multi-case correlation, operational monitoring and an
authenticated multi-user review workflow remain future milestones.
