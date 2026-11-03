# AEGIS-NHI · THE BEAST 🛡️

**Autonomous Chief Risk Officer & Cyber Risk Quantification**

> Capability is not authority. Evidence before action. Humans retain control.

**Status: v0.3 autonomous-perimeter and financial-frontier milestone.** The third-party-agent case, grant policy replay, seeded annual-loss model, three deterministic agent roles, bounded tool trace, local human-review ledger, tests and a redesigned five-view executive console are implemented on the feature branch. The other three planned cases, LLM-backed agent reasoning, and production integrations are NOT yet implemented.

All events, banks, non-human identities, costs and loss assumptions here are **synthetic**. This is not a deployed security system, production risk assessment, actual loss, or realized saving.

## Why

Bank risk leadership must distinguish what an agent can technically do from what it is authorized to do, evaluate credible downside assumptions and make decisions with traceable evidence.

## Two engines, three governed roles

**Engine 1: NHI / FinOps investigator.** Event-time scoped grants, denied actions, simulated runtime charges and bounded tools.

**Engine 2: Cyber risk quantification.** Seeded Poisson annual event frequency and triangular loss magnitude (FAIR-inspired scenario model), with sensitivity sliders. The analytical expected annual loss is conditional on hypothetical future control failures. P10, P50 and P90 are *outcome quantiles*, not confidence intervals.

**Three deterministic workflow roles (no LLM calls at v0.1):** FinOps Auditor, Risk Actuary, Executive Reporter. The explicit tool registry is read-only, capped and hashed.

Four planned banking scenarios: unauthorized third-party agent actions; cyber/data exposure; runaway AI spending; shadow AI. **Only unauthorized third-party agent actions are active so far.**

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

**FinOps & Agents:** Four bounded, allowlisted, read-only tool invocations and per-event synthetic charges. Runaway token/GPU detection is a roadmap item, **not implemented**.

**Cyber Risk Economics:** The exact seeded risk model now exports a 16-bin annual-loss histogram with separate zero-loss years and extreme tail. Control-economics comparison has editable effectiveness, one-time implementation and annual operating assumptions, three-year NPV at 10%, and optional simple payback. A frequency × effectiveness heatmap shows pure what-if sensitivity; it is not empirical incident data.

**Decision & Evidence:** Local human reviews are tied to the exact risk **and proposed-control cost** snapshot. Changing control assumptions therefore creates a distinct review record. Exports contain the input hashes, financial model, control economics, and available local review history.

Every financial comparison is **hypothetical, not booked savings, not actual loss avoidance, and not a real-bank risk estimate**. The original incident fixture still shows one authorized execution and three blocked unauthorized requests.

### Screenshot and browser QA

1. Run `uv sync --extra dev --extra dashboard`, then `uv run pytest -q`.
2. Run `uv run streamlit run streamlit_app.py` and inspect all five tabs.
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

## Next work

Pass CI; verify the app in a browser; publish actual screenshots; add the other three distinct synthetic cases and FinOps anomaly analytics; then optionally add model-based narrated investigation guarded by deterministic verification.

**Build the technology. Understand the economics. Earn the trust. Grow the business.**
