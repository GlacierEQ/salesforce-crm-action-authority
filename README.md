# CRM Action Authority

Independent GlacierEQ portfolio exhibit aligned to **Salesforce** operating themes.

> **Not affiliated.** This repository is not affiliated with, endorsed by, employed by, or deployed at Salesforce.
> No proprietary access, production deployment, customer impact, or company partnership is claimed.

## Bottleneck

Trusted autonomous action over CRM context and enterprise integration layers.

**Brick wall:** Preventing incorrect, over-scoped, replayed, or irreversible CRM actions while preserving identity, consent, reversibility, and business semantics.

## Implemented mechanism

**CRM Action Authority** is a deterministic, fail-closed authorization layer for CRM mutations.

It binds every admitted action to a fresh external grant containing:

- actor identity
- workflow/subject identity
- allowed CRM object types
- allowed action types
- field-level scopes
- issuance and expiry times
- a one-time nonce
- an explicit irreversible-action flag for external sends

### Action classes

- `CREATE`
- `UPDATE`
- `DELETE`
- `SEND_MESSAGE`

### Core guarantees

1. **No grant → no mutation.**
2. **Wrong actor, subject, object, action, or field scope → REFUSE.**
3. **Expired, future-dated, or replayed grants → REFUSE.**
4. **UPDATE requires a before-image for every changed field.**
5. **DELETE requires a before-image so a recreate receipt can be produced.**
6. **External sends are disabled by default.** They require explicit `SEND_MESSAGE` scope *and* `allow_irreversible=true`.
7. **Every allowed reversible mutation emits a reverse-operation receipt.**
8. **Non-finite or unsupported payload values fail closed rather than being stringified.**
9. **Receipts are deterministically SHA-256 bound to the authorized decision inputs.**

## Why this is technically interesting

The design combines capability attenuation, workflow provenance, replay control, reversibility, and deterministic receipts in one authorization boundary. A CRM agent can reason freely, but side-effect authority remains narrow and machine-verifiable.

`UPDATE` and `DELETE` are not merely permission-checked: they are refused unless a credible reverse operation can be constructed *before* admission. `SEND_MESSAGE` is modeled as an explicitly irreversible class rather than being treated as an ordinary field mutation.

See `ARCHITECTURE.md` for the expert design, threat model, receipt semantics, and production-boundary analysis.

## Sandbox campaign proof

`scripts/operate.py` exercises three concrete paths:

- scoped Lead status update → **ALLOW** with reverse UPDATE receipt
- identical campaign attempting an external message without a grant → **REFUSE**
- explicitly authorized one-time external send → **ALLOW**, marked non-reversible

This models an application-campaign CRM agent with a **no-send default**.

## Surfaces

| Surface | Path |
|---|---|
| Core mechanism | `src/crm_action_authority.py` |
| Direct operate path | `scripts/operate.py` |
| Behavioral tests | `tests/test_crm_action_authority.py` |
| Adversarial tests | `tests/test_adversarial.py` |
| Expert architecture | `ARCHITECTURE.md` |
| Verification matrix | `machine/verification-matrix.json` |
| Machine architecture | `machine/architecture.json` |
| Source-bound proof | `machine/implementation-proof.json` |
| Sanitized proof receipt | `machine/proof_receipt.json` |
| Operability receipt | `machine/operability_receipt.json` |
| Target contract | `machine/target-contract.json` |
| Excellence truth state | `machine/excellence-state.json` |
| Engineering handoff | `DEV_UP_INSTRUCTIONS.md` |

## Current proof state

The repository-local mechanism is **PROOF_REPRODUCED**.

- source-bound implementation proof: `machine/implementation-proof.json`
- canonical implementation source SHA: `0f81c93c94bfbf6cecf050d6b782ab7473b74bb2bddec8559506d38f29d1d4a6`
- behavioral cases: **8**
- domain adversarial cases: **10**
- total tests: **18/18 PASS**
- direct operate flow: **PASS**
- exact GitHub Actions source commit: `b31016add09695a113c2f78a2b266af92dec15c9`
- stale scaffold proof and leaf-local promotion authority: **removed**

Only estate-level gates remain before any future `PROMOTED` claim:

- external authenticated promotion authority
- canonical estate-position resolution

Those gates are intentionally outside the public leaf; the repository does not mint its own promotion authority.

## Non-claims

- No Salesforce employment, endorsement, proprietary data, production deployment, or customer impact
- No claim that these data structures reproduce Salesforce's internal authorization model
- No signing key or promotion secret is embedded in this public repository
- Green unit tests do not, by themselves, constitute external production authority
