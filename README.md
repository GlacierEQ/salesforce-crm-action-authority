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
| Target contract | `machine/target-contract.json` |
| Excellence truth state | `machine/excellence-state.json` |
| Engineering handoff | `DEV_UP_INSTRUCTIONS.md` |

## Current proof state

The domain mechanism is **IMPLEMENTED** and the stale Wave C generic promotion is revoked.

Promotion is intentionally withheld until:

- a current-head source-bound implementation proof is generated
- promotion authority is supplied externally rather than minted by the public leaf
- canonical estate position is resolved

## Non-claims

- No Salesforce employment, endorsement, proprietary data, production deployment, or customer impact
- No claim that these data structures reproduce Salesforce's internal authorization model
- No signing key or promotion secret is embedded in this public repository
- Green unit tests do not, by themselves, constitute external production authority
