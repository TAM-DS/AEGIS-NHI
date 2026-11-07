# AEGIS-NHI | Client engagement brief

**TAGM Client-to-Value Studio — risk engagement.** Fictional discovery and pilot
design, supported by a synthetic reference implementation. No client deployment,
real incident detection, measured loss reduction or autonomous remediation claimed.

## Decision to support

Can the risk team trace a non-human identity's requested action to its resource,
event-time grant, recorded outcome and supporting evidence quickly enough to
make a defensible human decision?

**Fictional buyer:** CRO of a mid-market bank. **Technical owners:** security
architecture, IAM and SOC. **Economic reviewer:** CFO. **Acceptance owner:** named
risk sponsor, appointed before a pilot.

## Discovery workshop — 45 minutes

| Time | Question | Required output |
|---|---|---|
| 0–10 | Which decisions stall because evidence is fragmented? | One investigation workflow and decision owner |
| 10–20 | Which system establishes identity, grant and observed outcome? | Source-of-truth map with access owners |
| 20–30 | What mistakes matter: false joins, missed evidence, wrong severity? | Failure costs and escalation rules |
| 30–40 | How long do comparable cases take today? | Baseline sampling plan |
| 40–45 | What evidence earns a pilot go/no-go? | Signed acceptance criteria and exclusions |

Qualify out if source access cannot be authorized, identities cannot be reconciled,
the sponsor expects automatic containment, or no reviewer can own the decision.

## Architecture alternatives

| Option | Best fit | Trade-off / discovery check |
|---|---|---|
| Extend existing SIEM/SOAR/IAM workflows | Existing tools already capture authoritative evidence | Verify licensing, query access and evidence export before building |
| Bounded custom evidence projection | A specific investigation needs transparent event-to-grant links | Requires schema ownership, source validation and maintenance |
| Wider enterprise platform | Multiple teams need governed entities and workflows | Higher integration and operating burden; require a separate business case |

**Reference recommendation:** prove one case-scoped workflow first. Use deterministic
rules for known authorization and evidence checks. Optional model narration must
remain grounded in those results; it must not create evidence or action authority.

## Proof-of-value demonstration

1. Load a repository-owned fictional scenario.
2. Export its case graph using the documented CLI.
3. Follow identity → event → resource and event → evidence relationships.
4. Contrast recorded execution, recorded block and policy authorization.
5. Verify the export against the independently selected original scenario.
6. Alter an edge or authority field and demonstrate verification failure.
7. Present a human recommendation with its assumptions and unresolved questions.

See [graph reproduction and verification](CYBER_DECISION_INTELLIGENCE.md).
This demonstration makes no external calls and does not join separate cases.

## Acceptance and evidence register

| Gate | Acceptance criterion | Evidence / status |
|---|---|---|
| Reproducibility | Same source and implementation produce the same graph | Graph unit tests and CI |
| Source consistency | Altered exports, even rehashed, fail verification | Source-verification regression tests |
| Provenance | Every edge points to known case-scoped nodes | Graph tests; synthetic fixtures only |
| Authority | Export remains NOT_AUTHORIZED_FOR_ACTION | Export fields and negative tests |
| Live source quality | Authorized, scoped feeds reconcile with source records | Not implemented |
| Cross-source joins | Explicit provenance and join keys; false joins rejected | Future ingestion contract |
| Operational reliability | Measured latency, volume, error rate and recovery | Not measured in a customer environment |
| Business value | Comparable baseline and assisted review measurements | Pilot design only |

For each pilot run record: run ID, UTC timestamp, code commit, fixture/source
version, input and graph hashes, test command, result, reviewer and exceptions.
Store sensitive source evidence in an access-controlled system; link to it.

## Economics — assumptions, not achieved savings

Measure baseline review minutes B, assisted review minutes A, monthly eligible
cases V, loaded analyst cost C/hour, recurring operating cost P/month and initial
implementation cost I.

Monthly capacity hours = max(B − A, 0) × V / 60.
Capacity value = capacity hours × C. Net modeled value = capacity value − P.
Simple payback = I / net modeled value only when net value is positive and the
buyer agrees that the capacity is financially realizable.

Keep expected cyber-loss modeling separate: event frequency, conditional impact,
control effectiveness and uncertainty require explicit assumptions and specialist
review. Do not add modeled avoided loss to staff capacity without addressing
overlap, attribution and uncertainty.

## Delivery and executive readout

- **Phase 1:** discovery, source inventory and acceptance agreement.
- **Phase 2:** offline replay, integrity checks and analyst walkthrough.
- **Phase 3:** separately scoped authorized source ingestion and join validation.
- **Phase 4:** limited pilot, baseline comparison, operating ownership and go/no-go.

Stop when provenance is unresolved, validation fails, scope expands without an
owner, or the business case depends on unverified avoided-loss claims.

**Five-minute readout:** decision needed → demonstrated evidence → remaining
uncertainty → options and costs → next gate and accountable owner.
