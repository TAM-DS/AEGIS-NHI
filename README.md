<p align="center"><img src="docs/images/aegis-nhi-explained.svg" width="100%" alt="AEGIS means Protective Shield. NHI means Non-Human Identity: AI agents, service accounts, APIs and automated workflows. Capability is not authority." /></p>

**AEGIS = protective shield. NHI = non-human identity.** The name means protecting and governing what software is *authorized* to do, with traceable evidence and human oversight.

---

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

**Status: v0.5 synthetic reference milestone.** Four distinct fictional investigations, deterministic governance, evidence-grounded narration, a seven-view Streamlit dashboard, human recommendation review and automated tests are implemented in the v0.5 reference milestone. This is not a deployed security system, live bank monitor, certified risk assessment, or a claim of actual prevented losses.

All events, banks, non-human identities, costs and modeled losses are **synthetic**. Agent roles are deterministic functions, not autonomous LLM agents; external model selection is optional and explicitly user-initiated.

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

## Two analytical engines. Three governed roles. Four investigations.

**Engine 1 — NHI and FinOps investigations:** retrospective scoped authorization, ledger reconciliation, runaway-agent tool-call forensics, protected-data rules, declared-region metadata, and shadow-AI identity/tool inventory.

**Engine 2 — Cyber risk quantification:** bounded, seeded Poisson annual frequency and triangular event severity. Expected annual loss and P10/P50/P90 are *hypothetical annual outcome figures*, not real losses or statistical confidence intervals. Proposed control economics are scenario assumptions, not validated ROI.

**Three deterministic roles:** FinOps Auditor, Risk Actuary, and Executive Reporter; all workflow tools are allowlisted, read-only and bounded. The optional model can only select verified executive claim IDs; it cannot add new facts or approve any action.

**Four working fictional scenarios:** BANK-NHI-001 (authorization); BANK-FINOPS-002 (runaway tools); BANK-DATA-003 (restricted-data exposure); BANK-SHADOW-004 (unregistered identities/tools).

[Technical architecture and scope](docs/ARCHITECTURE.md)

## Quick start · Offline by default

Clone the default branch and run the seven-view executive app:

    git clone https://github.com/TAM-DS/aegis-nhi.git
    cd aegis-nhi
    uv sync --extra dev --extra dashboard
    uv run pytest -q
    uv run python -m aegis_nhi.cli --output artifacts/nhi_demo_report.json
    uv run streamlit run streamlit_app.py

Or use a standard Python environment:

    python -m pip install -e ".[dev,dashboard]"
    python -m pytest -q
    python -m streamlit run streamlit_app.py

The entire baseline needs **no API key, live bank, cloud account or paid service**. Named human reviews are stored in the local gitignored SQLite file at .aegis/reviews.sqlite3. Optional model-ordered claim cards require the extra narration package, a locally configured OPENAI_API_KEY, and a manual click; no model calls occur by default.

## First case: BANK-NHI-001

- One authorized synthetic account-summary read is recorded as executed.
- An attempted transfer without a scoped resource grant is recorded as blocked.
- A bulk-export request without the permitted action is recorded as blocked.
- A read request after grant expiry is recorded as blocked.

**Recorded synthetic tool charges:** $0.016 — not an invoice.

**Hypothetical modeled annual exposure:** 1.7 annual events, $80,000 minimum / $200,000 mode / $900,000 maximum synthetic severity; the resulting analytical expected annual loss at baseline is **$668,666.67**. This is NOT an observed or prevented loss; it is a counterfactual scenario if controls fail in the future, not the financial consequence of the blocked event.

## Four completed synthetic investigations · v0.5

| Case | Business problem | Tested fixture result |
|---|---|---|
| **BANK-NHI-001 — Agent authority** | What can an AI agent do under its scoped human-approved grant? | One authorized read, three recorded blocks, event-time replay and source evidence |
| **BANK-FINOPS-002 — Runaway agent** | Can authorized calls escalate into unsafe operational behavior and cost? | 600 calls / six minutes versus 12 normal calls (50×), bounded rule detectors, separately scoped token and GPU estimates |
| **BANK-DATA-003 — Sensitive-data exposure** | Are restricted actions or declared regions outside policy? | Blocked bulk export plus a separately recorded, fictional executed region-policy exception |
| **BANK-SHADOW-004 — Shadow AI** | Can an approved identity still use an unregistered AI tool? | Detects unknown AI identities separately from unknown AI tools; compares executed and blocked synthetic events |

**An attempted action is not an executed action.** An executed *synthetic* event is not an actual breach or live monitoring proof. Hypothetical expected loss is not money lost or saved.

## Seven working executive views

1. **Executive Authority:** concise fictional incident briefing, timeline and annual risk context.
2. **Autonomous Perimeter:** identity-to-action Sankey, scoped grants, policy replay, declared data destination metadata.
3. **Ledger & FinOps:** fictional ledger reconciliation, bounded read-only tool traces, synthetic costs.
4. **Agent Forensics:** repeated calls, first rule alert, call-budget amplification, what-if cost exposure.
5. **Capital at Risk:** seeded loss distributions, percentiles, hypothetical control-economics and sensitivity.
6. **Audit & Decisions:** named human reviews attached to exact source and economic scenarios, exportable audit evidence.
7. **Scenario Lab:** interactive data-exposure and shadow-AI cases, evidence-grounded findings, executive narration, case-specific human review.

The published six-view screenshot gallery is actual v0.4 app output. The seventh tab is implemented and covered by an automated Streamlit render test; its visual capture should be taken from the running v0.5 app.

## Evidence-locked executive narration

A controlled Python generator creates plain-English claims from validated scenario evidence and separately sourced risk assumptions. Every claim carries relevant evidence IDs or a source scenario-assumption hash. No unconstrained model text is displayed.

**Optional model feature:** An explicitly clicked button may send *fictional claim cards* to the external API to choose a limited subset of existing claim IDs. The client requests at most 180 output tokens, 12-second timeout and no retry per manual invocation. Unknown IDs, duplicate IDs, extra fields and model-authored prose fail closed; the deterministic briefing remains available. Neither mode can authorize cloud, bank, data, network or IAM actions.

Enable optional claim selection only when you want to use it:

    uv sync --extra dev --extra dashboard --extra narration
    # Configure OPENAI_API_KEY locally. Never commit it.
    uv run streamlit run streamlit_app.py

## The architecture and its boundaries

- **Deny-by-default replay:** identity → resource → action → event-time signed-off grant → retrospective allow/deny with evidence.
- **Financial judgment:** model annual frequency/severity using reproducible seeded simulation; distinguish baseline, residual, assumed effectiveness, implementation cost, annual cost and discounted modeled value.
- **Human governance:** reviewer, rationale, decision status and exact snapshot; approval never performs an operational action.
- **Provenance:** versioned JSON fixtures, source and tool-output SHA-256 hashes, bounded tools, deterministic tests, GitHub Actions and downloadable JSON evidence.
- **Scope:** no real bank integration, deployed security monitoring, operational enforcement, live data export, exfiltration proof, observed fraud losses, actual cloud bills or autonomous remediation.

Framework references: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) · [OWASP GenAI Security](https://genai.owasp.org/) · [FAIR Institute](https://www.fairinstitute.org/). References do not imply compliance or certification.

---

### THE BEAST · Guard the gates. Keep human authority.

**Deconstruct the authority. Quantify the exposure.**

**Build the technology. Understand the economics. Earn the trust. Grow the business.**
