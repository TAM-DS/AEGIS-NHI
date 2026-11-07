# Cyber Decision Intelligence · Phase 0

**Status: tested single-scenario synthetic evidence graph; not a deployed security platform or cross-repository integration.**

The new `aegis_nhi.cyber_graph` module projects validated AEGIS-NHI event and policy evidence into **case-scoped nodes and directed relationships**. This begins the Palantir-inspired *data → connected entities → governed decision* demonstration without claiming use of Palantir Foundry, Gotham, AIP, or an operational Ontology.

## Current proof

- Graph nodes: fictional case, non-human identities, resources, grants, events, evidence sources, tool identifiers (when declared), and specialized policy findings.
- Graph edges: requested action, targeted resource, matched runtime grant, original supporting evidence, and a rule finding's linked event.
- Event outcomes remain **blocked** or **executed in the fictional fixture**, never real-world transactions, data exposures or prevented breaches.
- A recorded region-policy exception remains a **synthetic policy exception**, not evidence of real exfiltration.
- Source case SHA-256 plus deterministic graph SHA-256 support reproducibility; these are not digitally signed, independently immutable records.
- Every edge references a known case-scoped node. Distinct scenarios are deliberately **not silently joined** on similar labels or entities.

## Reproduce

```bash
uv sync --extra dev --extra dashboard
uv run pytest -q tests/test_cyber_graph.py
uv run python -m aegis_nhi.cyber_graph --scenario data/scenarios/sensitive_data_exposure.json --output artifacts/cyber_graph.json
```

The exported artifact is a JSON *reference graph*, not an interactive product UI. No external system, broker, IAM, security platform, telemetry stream, bank, or model endpoint is called.

## Next acceptance gates

1. Define an explicit and testable **cross-source ingestion contract** before incorporating AEGIS Analyst, SENTINEL, or AEGIS Evidence fixtures.
2. Require verified case/source provenance and explicit join keys. Never equate IDs across fictional institutions or silently correlate events by timestamps alone.
3. Show identity → event → asset → evidence investigations in an analyst-facing view without adding autonomous remediation.
4. Add acceptance tests for duplicate/conflicting identifiers, missing/contradictory evidence and cross-source contamination.
5. Create a consulting discovery, architecture, build-versus-buy and client-readout package with clearly modeled business impact.

**Human authority boundary:** This graph cannot approve a recommendation, grant permissions, isolate a host, move funds, deploy agents, or change any connected system.

## Verify a saved graph against its source

Exported hashes are reproducibility aids, not signatures. A changed export can
be given a new, self-consistent hash. The verifier therefore rebuilds the entire
graph from an independently selected source case and compares the full JSON
projection, including evidence relationships, counts and authority status.

```bash
uv run python -m aegis_nhi.cyber_graph --scenario data/scenarios/shadow_ai.json --output artifacts/shadow_graph.json
uv run python -m aegis_nhi.cyber_graph --scenario data/scenarios/shadow_ai.json --verify artifacts/shadow_graph.json
```

A successful verification means only that the export matches that synthetic
source and this implementation. It does not establish that the source is true,
signed, independently preserved, or authorized for action. A mismatch fails
with a nonzero exit status. Select the source independently; replacing both
the source and export is outside this integrity check.

[Client discovery and proof-of-value engagement](CLIENT_ENGAGEMENT.md)
