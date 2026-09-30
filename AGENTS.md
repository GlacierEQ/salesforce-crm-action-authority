# AGENTS.md — salesforce-crm-action-authority

**Company:** Salesforce
**Domain:** Enterprise Data Platform & Authority Governance

## Quick Rules
- **Test command:** `PYTHONPATH=src pytest tests/ -v`
- **Lint:** `ruff check src/ tests/`
- **No drive-by edits** — load the skill first.

## Architecture
- `src/salesforce_crm_action_authority/core.py` — Domain logic (Enterprise Data Platform & Authority Governance)
- `tests/` — Verified test suite
- `.github/workflows/ci.yml` — Enforced CI pipeline
