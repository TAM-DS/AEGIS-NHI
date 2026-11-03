## From the headlines

> **Fictional composite inspired by real reporting.** The bank, customer, account activity, password reset, external payee, six-figure transfer, and human intervention in this story are invented—not a reported incident. AEGIS-NHI uses synthetic cases and does not claim to have detected or prevented an actual bank transaction.

### The Agent That Looked Like the Customer

It was a Tuesday morning in late October when the first alerts lit up the risk desk.

A mid-market commercial bank had been watching a quiet pattern for weeks: third-party AI agents logging into customer accounts with valid credentials. Most performed the expected tasks—balance checks, statement pulls, routine payments. Then one agent stopped following the script.

It reset a password. It added a new external payee. It initiated a six-figure transfer. Every step used legitimate session tokens. To the core banking system, the agent looked exactly like the customer.

No one could immediately prove otherwise. The customer had handed over credentials to a personal-finance agent weeks earlier. This fictional bank had no scoped grant, no event-time authority check, no reliable way to separate *what the software could technically do* from *what it was still authorized to do*. The transfer was stopped only because a human reviewer happened to notice the velocity spike before the funds left the rail.

In the fictional bank's subsequent risk committee review, one question landed with force:

**If an autonomous agent can inherit a customer's full privileges, how do you prove—before the money moves—that the action is still inside the grant the human actually approved?**

**That question is why this project exists.**

**The real headlines behind the scenario:** On October 22, 2026, [Axios](https://www.axios.com/2026/10/22/ai-agents-banks-unauthorized-accounts-access) reported U.S. banks detecting unvetted third-party AI agents in customer accounts and restricting their access, naming Morgan Stanley, JPMorgan, Bank of America and Citi among the institutions responding to this risk. [Reuters](https://www.reuters.com/legal/government/us-banks-detect-unauthorized-ai-agents-customer-accounts-axios-reports-2026-10-22/) also reported banks blocking agents, while noting that Morgan Stanley had **not** observed rogue AI activity on its platforms. Separately, the [Financial Stability Board's October 15, 2026 sound practices](https://www.fsb.org/2026/10/fsb-finalises-sound-practices-for-the-responsible-adoption-of-artificial-intelligence-ai/) emphasize effective human oversight, AI governance and risks involving third-party AI dependencies. **None of these sources reports the fictional transfer described above.** “Capability is not authority” is AEGIS-NHI's own design principle, not an attributed regulatory quotation.

**That near-miss is the reason the perimeter now has a guardian.**

---

# AEGIS-NHI · THE BEAST 🛡️

<img src="docs/images/aegis-beast-guardian.png" alt="The Beast: armored black cat with neon blue eyes and a mace-shaped tail" width="110" align="right" />

**Meet The Beast:** a little black-cat guardian of the autonomous perimeter, with crusader armor, neon-blue eyes, white claws and a mace-shaped tail. He belongs in the app sidebar because a memorable product identity matters alongside tested engineering.


**Autonomous Chief Risk Officer & Cyber Risk Quantification**

> Capability is not authority. Evidence before action. Humans retain control.

**Status: v0.4 autonomous-agent forensics milestone.** The third-party-agent case, grant policy replay, seeded annual-loss model, three deterministic agent roles, bounded tool trace, local human-review ledger, tests and a six-tab executive console are implemented on `main`. Two of four planned synthetic investigations are implemented (unauthorized agent actions and runaway agent forensics); the cyber/data-exposure and shadow-AI cases, LLM-backed agent reasoning, and production integrations are NOT yet implemented.

All events, banks, non-human identities, costs and loss assumptions here are **synthetic**. This is not a deployed security system, production risk assessment, actual loss, or realized saving.

## The Beast in action · Six executive views

**A product you can inspect—not just a promise you have to believe.** These are real screenshots from the running **AEGIS-NHI v0.4 Streamlit application**, using entirely fictional banking fixtures, deterministic control evidence and hypothetical financial assumptions.

### 01 / Executive Authority — Deconstruct the authority. Quantify the exposure.

[![Executive Authority dashboard with AEGIS-NHI guardian branding, synthetic incident metrics and board-level risk briefing](docs/images/Executive_Authority-01.png)](docs/images/Executive_Authority-01.png)

*The 30-second executive assessment: four synthetic requests, three blocked actions and zero recorded unauthorized executions—alongside a clearly separate, hypothetical annual risk scenario.*

### The perimeter and the ledger

| **02 / Autonomous Perimeter** | **03 / Ledger & FinOps** |
|:---:|:---:|
| [![Autonomous Perimeter identity-to-action Sankey diagram with authorized and blocked synthetic actions, policy replay, and jurisdiction checks](docs/images/Evidence_Chain-04.png)](docs/images/Evidence_Chain-04.png) | [![Ledger and FinOps dashboard showing synthetic reconciliation, bounded read-only tool traces and incident cost evidence](docs/images/Financial_Frontiers-05.png)](docs/images/Financial_Frontiers-05.png) |
| **Follow the authority.** Identity → scoped action → observed outcome, with evidence for every allow or deny. | **Follow the money.** Reconcile fictional ledger evidence and distinguish synthetic tool charges from invoices or modeled losses. |

### 04 / Agent Forensics — Audit the behavior. Expose the cost. Govern the consequence.

[![Agent Forensics dashboard with six-minute simulated runaway tool use, 600 calls, fifty-times normal amplification, trend chart, repeated calls and detection findings](docs/images/Audit_Behaviors-06.png)](docs/images/Audit_Behaviors-06.png)

*The technical centerpiece: a synthetic third-party agent makes 600 calls against a 12-call normal workflow (50×). Deterministic detectors flag sustained bursts, call-budget breaches, and repeated tool signatures. An authorized individual tool call is **not** an unlimited operational mandate.*

### Quantify the downside. Retain human judgment.

| **05 / Capital at Risk** | **06 / Audit & Decisions** |
|:---:|:---:|
| [![Capital at Risk dashboard with seeded 5000-year annual loss distribution, proposed control comparison and hypothetical net-value economics](docs/images/Capital_Risk-08.png)](docs/images/Capital_Risk-08.png) | [![Audit and Decisions view showing evidence integrity, a pending human recommendation review, reviewer rationale fields and traceable synthetic evidence cards](docs/images/Audit_Governance-10.png)](docs/images/Audit_Governance-10.png) |
| **Price the control.** Compare modeled annual exposure, simulated loss distributions and assumption-based control economics. | **Govern the consequence.** Bind decisions to evidence and human-review records; do not confuse recommendation approval with operational permission. |

<details>
<summary><strong>Explore three closer investigations: event timeline, forensic evidence and executive economics</strong></summary>

#### A. Exactly which actions were blocked?

[![Time-ordered synthetic authorization event timeline with one permitted read and blocked transfer, export and expired-grant read](docs/images/Agentic_Mutation_Evidence-02.png)](docs/images/Agentic_Mutation_Evidence-02.png)

*Time-ordered replay of one authorized read and three blocked requests. This is offline synthetic evidence, not live bank enforcement.*

#### B. When did the detector notice the runaway calls?

[![Agent Forensics detailed findings showing first-alert minute, rule-to-evidence links, token and GPU assumptions, bounded continuation projections and human review](docs/images/Forensic_Findings-07.png)](docs/images/Forensic_Findings-07.png)

*Rules, evidence IDs, unit-rate assumptions, additional-time projections and a pending human investigation decision. Token and GPU cost estimates may overlap and are **not additive**.*

#### C. What decision would an executive need to make?

[![Executive briefing with what-happened summary, hypothetical residual annual exposure, governance decision and synthetic ledger boundary status](docs/images/What-Could-It-Cost-03.png)](docs/images/What-Could-It-Cost-03.png)

*A business-facing view of what happened, what it might mean economically under assumed future conditions, and what still requires a human.*

</details>

**Evidence boundary:** These screenshots use synthetic scenarios and selectable assumptions. They do not show a real bank incident, deployed agent monitoring, prevented losses, billable cloud charges or approved production remediation. The [source image directory](docs/images) contains all ten captured screenshots; the earlier **Investment Committee** close-up is intentionally not featured because it predates a financial-text rendering correction. Refresh that capture from the current app before publishing it as an official product view.

---

## Why

Bank risk leadership must distinguish what an agent can technically do from what it is authorized to do, evaluate credible downside assumptions and make decisions with traceable evidence.

## Product-building mindset: From market signal to release

AEGIS-NHI was approached as an end-to-end enterprise product, not just a technical demonstration:

1. **Market intelligence:** Identify genuine banking pain points through industry discussions and research.
2. **Product strategy:** Translate those problems into capabilities executives would value.
3. **Architecture:** Design identity governance, forensic detection, risk quantification, and human oversight.
4. **Engineering:** Build functional software with deterministic logic, testing, and evidence.
5. **Financial intelligence:** Connect technical decisions to modeled business consequences and investment trade-offs.
6. **Product experience:** Make complex information understandable to a CRO, CFO, or CEO.
7. **Brand identity:** Create a memorable, cohesive product that people recognize.
8. **Delivery discipline:** Validate, test, document, and refine before release.

**Product principle:** Start with the business problem. Make authority explicit, quantify the assumptions, preserve the evidence, and earn the trust.

## Two engines, three governed roles

**Engine 1: NHI / FinOps investigator.** Event-time scoped grants, denied actions, simulated runtime charges and bounded tools.

**Engine 2: Cyber risk quantification.** Seeded Poisson annual event frequency and triangular loss magnitude (FAIR-inspired scenario model), with sensitivity sliders. The analytical expected annual loss is conditional on hypothetical future control failures. P10, P50 and P90 are *outcome quantiles*, not confidence intervals.

**Three deterministic workflow roles (no LLM calls at v0.1):** FinOps Auditor, Risk Actuary, Executive Reporter. The explicit tool registry is read-only, capped and hashed.

Four planned banking scenarios: unauthorized third-party agent actions; cyber/data exposure; runaway AI spending; shadow AI. **Unauthorized third-party agent actions and runaway AI spending are now separate, working synthetic investigations.**

[Full architecture blueprint](docs/ARCHITECTURE.md)

## Quick start: Mac and Python 3.13

Clone or pull the feature/beast-foundation branch, then run these commands in the repository folder:

    uv sync --extra dev --extra dashboard
    uv run pytest -q
    uv run python -m aegis_nhi.cli --output artifacts/nhi_demo_report.json
    uv run streamlit run streamlit_app.py

Or use a normal Python virtual environment:

    python -m pip install -e ".[dev,dashboard]"
    python -m pytest -q
    python -m streamlit run streamlit_app.py

No API keys, bank accounts, cloud accounts or paid services. Reviewer decisions are stored only in local gitignored .aegis/reviews.sqlite3.

## First case: BANK-NHI-001

- One authorized synthetic account-summary read is recorded as executed.
- An attempted transfer without a scoped resource grant is recorded as blocked.
- A bulk-export request without the permitted action is recorded as blocked.
- A read request after grant expiry is recorded as blocked.

**Recorded synthetic tool charges:** $0.016 — not an invoice.

**Hypothetical modeled annual exposure:** 1.7 annual events, $80,000 minimum / $200,000 mode / $900,000 maximum synthetic severity; the resulting analytical expected annual loss at baseline is **$668,666.67**. This is NOT an observed or prevented loss; it is a counterfactual scenario if controls fail in the future, not the financial consequence of the blocked event.

## Executive command center · v0.2

**Executive Command:** Large-format 30-second CRO/CFO briefing, source-linked timeline, recorded control decisions, and a distinct hypothetical annual exposure figure.

**NHI & Authorization:** Sankey-style identity → resource/action → decision map, source evidence tables and valid/expired scope checks. The diagram depicts *fictional requests*, not bank network traffic.

**FinOps & Agents (v0.2 baseline):** Four bounded, allowlisted, read-only tool invocations and per-event synthetic charges in BANK-NHI-001. The separately implemented v0.4 Agent Forensics case adds anomaly rules over fictional call and token/GPU telemetry; it is not a production cost monitor.

**Cyber Risk Economics:** The exact seeded risk model now exports a 16-bin annual-loss histogram with separate zero-loss years and extreme tail. Control-economics comparison has editable effectiveness, one-time implementation and annual operating assumptions, three-year NPV at 10%, and optional simple payback. A frequency × effectiveness heatmap shows pure what-if sensitivity; it is not empirical incident data.

**Decision & Evidence:** Local human reviews are tied to the exact risk **and proposed-control cost** snapshot. Changing control assumptions therefore creates a distinct review record. Exports contain the input hashes, financial model, control economics, and available local review history.

Every financial comparison is **hypothetical, not booked savings, not actual loss avoidance, and not a real-bank risk estimate**. The original incident fixture still shows one authorized execution and three blocked unauthorized requests.

### Screenshot and browser QA

1. Run `uv sync --extra dev --extra dashboard`, then `uv run pytest -q`.
2. Run `uv run streamlit run streamlit_app.py` and inspect all six tabs.
3. Change effectiveness and control cost: residual modeled exposure and NPV must change, while the event timeline and allowed/denied decisions remain identical.
4. Open Decision & Evidence, record an approval with named reviewer and rationale, then change the proposed control cost. Verify the *new* scenario remains pending human review; return to the previous inputs to see the original review.
5. Export JSON and confirm `human_review_history`, `hypothetical_control_economics`, and the original authorization evidence are present.

Screenshots should be captured from the functioning app **after local visual QA**, not fabricated marketing mockups.

## Controls and limitations

- Deny-by-default scope, action and event-time grant replay; recorded unauthorized executions are flagged.
- Seeded model reruns and bounded hypothetical loss assumptions.
- Allowlisted tools with per-case call budget and SHA-256 output traces.
- Synthetic fixture charges are **never added** to annualized cyber-risk figures.
- Human reviews are local audit entries, not operational approvals.
- Not a certified FAIR calculation, live banking implementation, or claim of NIST compliance.

References: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), [OWASP GenAI Security](https://genai.owasp.org/), [FAIR](https://www.fairinstitute.org/).

## Institutional authority intelligence · v0.3

**Deconstruct the authority. Quantify the exposure.**

*Audit the autonomous perimeter. Govern proposed agentic mutations, reconcile financial evidence, and stress-test modeled capital-at-risk before human review.*

This milestone adds two **synthetic, offline** features without a bank connection:

- **Ledger reconciliation:** check fictional opening/closing snapshots against any modeled double-entry postings. Correlate postings to recorded executed tool actions and their NHI authorization replay. A blocked request with a journal posting is flagged; divergent balances are not silently ignored. Baseline case BANK-NHI-001 has **zero journal postings**, not a prevented dollar loss.
- **Sovereign-routing policy replay:** compare declared simulated destination-region metadata with a US-only processing allowlist. A bulk-export attempt declares an EU destination and is blocked in the original event fixture. This is a policy comparison, **not real network routing or country-level regulatory compliance**.

The executive UI now uses "Autonomous Perimeter," "Ledger & FinOps," "Capital at Risk," and "Audit & Decisions." It distinguishes retrospective governance evidence from actual runtime enforcement. **No transaction signing, real bank ledger reconciliation, live sovereign routing, or immutable audit infrastructure is implemented.** SHA-256 hashes are not cryptographic approval signatures.

## Investment Committee Interpretation

The **Capital at Risk** screen now translates the synthetic risk distribution into a dynamic institutional decision narrative. Four clarified metrics distinguish baseline (without the *proposed additional* control), residual exposure (assuming the proposed control), median P50 outcomes and P90 severe outcomes. No amount is an observed bank loss.

The investment panel updates its modeled annual risk reduction, first-year net modeled value, three-year discounted net modeled value and **conditional** investment signal when proposed effectiveness or cost inputs change. Human review applies only to the exact evidence and cost snapshot. Neither a positive model signal nor recorded recommendation approval authorizes a real-world security or financial operation.

The six complementary views span Executive Authority, Autonomous Perimeter, Ledger & FinOps, Agent Forensics, Capital at Risk, and Audit & Decisions. They separate retrospective fixture evidence, modeled assumptions, and human decision authority.

## Autonomous Agent Forensics · v0.4

**Audit the behavior. Expose the cost. Govern the consequence.**

A new **Agent Forensics** executive tab investigates synthetic case **BANK-FINOPS-002** from the versioned data/scenarios/runaway_agent.json fixture. All data are fictional and no real banking system is contacted.

- **Observed fixture:** Six consecutive minute buckets contain 600 synthetic research-tool calls versus 12 normal calls per workflow (50× amplification), 570 identical-signature calls (95%), one million input tokens, 441,000 output tokens and six fictional GPU minutes.
- **Detectors:** Consecutive burst above the normal per-minute rate, cumulative workflow-call budget overrun, repeated-signature concentration, and independent detection of recorded execution outside a scoped NHI grant. Findings link to evidence and first-detection minute.
- **Financial evidence:** Model token cost using hypothetical pricing of synthetic token counts; price GPU-meter use separately. These providers' cost scopes can overlap and **must never be added together** or called invoiced spend.
- **Forward sensitivity:** Additional 1–24 hours are linearly extrapolated from six synthetic observed minutes; changing a rate or horizon does not mutate source events. This is not a production forecast or promised cost saving.
- **Review governance:** A reviewer approves or rejects the *investigation recommendation* for an exact pricing, threshold and horizon snapshot. No automated stop, credential action, cloud mutation or bank transaction exists.
- **Tests:** Bounded inputs, deterministic evidence reconciliation, alert rules, sensitivity separation, scoped authorization replay and a render smoke test.

The incident demonstrates that **individual tool calls can remain within a grant while workflow behavior becomes unsafe**. The platform identifies the modeled concern; it does not claim autonomous enforcement.

## Next work

The v0.4 screenshots and six-view evidence gallery are published above. Next: build the remaining distinct cyber data-exposure and shadow-AI synthetic scenarios, then optionally add bounded model narration only after deterministic evidence verification.

**Brand asset note:** The repository includes a compact transparent PNG derivative for application use. The original high-resolution artwork remains separate. The mascot was developed with AI assistance; no copyright registration or exclusive rights are claimed here.

**Build the technology. Understand the economics. Earn the trust. Grow the business.**
