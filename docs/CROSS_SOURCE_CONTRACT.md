# Cross-source evidence contract v1

**Implemented: bounded offline normalization and explicit linking of fictional
observations. No live feeds or adapters to other AEGIS repositories are connected.**

The module `aegis_nhi.source_contract` validates a complete bundle before producing
a report. It is a separate ingestion boundary; it does not merge observations
into the existing case graph or grant permission to act.

## Reproduce the two-source demonstration

From the repository root in the installed project environment:

```bash
python -m aegis_nhi.source_contract data/cross_source/two_source_demo.json --source fictional-iam --source fictional-audit
python -m pytest -q tests/test_source_contract.py
```

Expected counts: **2 observations, 1 explicit event link**. The CLI returns zero
on success and one with a sanitized rejection message for invalid input. It makes
no network calls. Output remains `NOT_AUTHORIZED_FOR_ACTION` with provenance
`DECLARED_NOT_AUTHENTICATED`.

## Exact v1 schema

Unknown and missing fields are rejected. IDs use 1–128 ASCII letters, numbers,
underscores, periods or hyphens and must start with a letter or number.

| Object | Required fields |
|---|---|
| Bundle | schema_version (integer 1), synthetic (boolean true), records, links |
| Observation | source_id, record_id, institution_id, case_id, identity_id, resource_id, action, outcome, evidence |
| Evidence | evidence_id, sha256 (64 lowercase hexadecimal characters) |
| Link | left, right, relation, basis_evidence |

Observation keys are `(source_id, record_id)`; record IDs must be unique within
each source in a bundle. Identity and resource IDs remain source-local labels.
The allowlist is supplied independently by the operator, not accepted from the
bundle. An allowlisted name does not authenticate a sender.

`left` and `right` are `[source_id, record_id]`. The only supported relation is
`SAME_REPORTED_EVENT`. Each basis reference is `[source_id, record_id, evidence_id]`.
The link must reference evidence from **both** endpoint records. Evidence belonging
to an unrelated record cannot justify a link.

## Link and conflict rules

- Sources must differ; both endpoints must exist.
- Institution and case IDs must match exactly. These shared scopes must be assigned
  by a future trusted normalization adapter; matching text alone is not proof.
- Action and recorded outcome must agree. Outcomes are `executed` or `blocked`.
- Duplicate observations, duplicate evidence IDs within a record, duplicate links
  and duplicate link-evidence references are rejected.
- Equal names, timestamps or identity labels never create an inferred link.
- A link records a declared same-event association. It does not collapse identity
  or resource IDs, reconcile people, or establish a true causal relationship.

Limits: 1 MiB JSON input, 1–1,000 observations, at most 1,000 links, 1–20 evidence
items per observation, and 2–40 basis references per link. CLI JSON duplicate keys
are rejected. Any invalid record or link rejects the whole bundle; no partial
success or automatic retries are emitted.

## Provenance and reproducibility

The report preserves evidence digest declarations and sorts observations, evidence
and links for deterministic output. Input record order and link direction do not
change the report. `report_sha256` is a consistency aid, not a signature.

The example evidence digests are hashes of invented strings, not external evidence
files. V1 checks digest syntax, not bytes fetched from a source. A future adapter
must authenticate source identity, verify source bytes and immutable revision,
establish institution/case scope, and preserve timestamp semantics before use.

## Five-minute client walkthrough

1. **Problem:** matching labels across systems can create a false investigation.
2. **Demonstrate:** run the fixture and inspect two separate source records plus
   the explicit evidence-backed link.
3. **Negative case:** change the second institution ID and run again: the bundle
   is rejected. Restore it, change outcome to `blocked`, and show conflict rejection.
4. **No inference:** remove links and rerun: identical labels yield zero links.
5. **Decision:** approve a separately scoped adapter pilot only after provenance,
   authoritative case mapping and analyst review criteria are agreed.

## Acceptance boundary and remaining work

Tests cover valid links, ordering, unknown sources, cross-case/institution links,
contradictory observations, malformed evidence, bounds, duplicate identifiers and
CLI rejection. They do not establish real-world source authenticity or detection
accuracy. Real repository adapters, case-graph integration, analyst UI and live
connectors remain future gates. No automatic remediation is introduced.

[Client engagement](CLIENT_ENGAGEMENT.md) · [Existing case graph](CYBER_DECISION_INTELLIGENCE.md)
