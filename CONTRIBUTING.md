# Contributing to AEGIS-NHI

Thank you for helping others learn from and improve this open-source reference.

**What to share:** Your use case, what you changed, why it matters, what trade-offs you encountered, test results or screenshots from your own functioning version, and what you learned. Public contributions are welcome but entirely voluntary under the MIT License.

## Ways to participate

1. [Open a GitHub issue](https://github.com/TAM-DS/aegis-nhi/issues/new) describing a suggestion, bug, question, or your adaptation. Explain the business problem and the evidence supporting the change.
2. Fork the repository and create a feature branch for code or documentation changes. Include reproducible synthetic fixtures and tests where appropriate.
3. If you'd like your improvement incorporated upstream, open a pull request describing the decision, trade-offs, controls, evidence and business consequence.

## Local validation

```bash
uv sync --extra dev --extra dashboard
uv run pytest -q
uv run python -m aegis_nhi.cli --output artifacts/nhi_demo_report.json
uv run streamlit run streamlit_app.py
```

The baseline runs without any cloud or bank credentials. The optional AI narration feature requires separate manual opt-in and configuration.

## Engineering and safety boundaries

- Only commit fictional or synthetic test data. **Never commit client, customer, banking, employee, financial-account or credential information.**
- Keep observed synthetic events separate from hypothetical risk projections, forecasts and assumed financial loss.
- Preserve grant/replay boundaries, evidence links, human recommendation review and deterministic fail-closed behavior.
- Do not claim the project is a deployed DLP, security monitor, production autonomous CRO, regulator-certified framework, or a service that prevented actual losses.
- Never upload secrets or claim security assessment or production readiness without documented, independently verifiable evidence.

## Licensing and attribution

This project is available under [MIT](LICENSE). Keep the copyright/license notice when sharing copies or substantial portions. You are **not required to share private changes** or publish your fork, but we'd love to learn what worked and what you improved.

**Build the technology. Understand the economics. Earn the trust. Grow the business.**
