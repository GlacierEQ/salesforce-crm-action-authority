# Engineering Handoff — CRM Action Authority

## Current phase

`PROOF_REPRODUCED` is the intended repository-local completion state after the source-bound finalizer and CI pass.

The portfolio mechanism is no longer a scaffold. It implements deterministic CRM action authorization with scoped external grants, replay prevention, reverse-operation receipts, explicit irreversible-send authority, and fail-closed canonicalization.

## Preserve these invariants

1. No grant means no mutation.
2. Grants bind actor, workflow subject, object, action, fields, time window, and one-time nonce.
3. UPDATE and DELETE are inadmissible when a reverse operation cannot be constructed from before-state.
4. SEND_MESSAGE is an explicit irreversible class and requires `allow_irreversible=true`.
5. Non-finite values and unsupported canonical types fail closed.
6. Decision receipts remain deterministic and input-bound.
7. The public leaf must never mint its own promotion authority or embed a reusable signing secret.
8. No Salesforce affiliation, proprietary implementation, production deployment, or customer-impact claim may be introduced without independent evidence.

## Proof surfaces

- `tests/test_crm_action_authority.py` — behavioral contract
- `tests/test_adversarial.py` — attack/fail-closed contract
- `scripts/operate.py` — direct end-to-end sandbox decision flow
- `machine/implementation-proof.json` — source-tree-bound proof
- `machine/proof_receipt.json` — sanitized CI receipt
- `machine/operability_receipt.json` — direct operate receipt
- `machine/verification-matrix.json` — threat-to-test mapping
- `ARCHITECTURE.md` — expert design and production-boundary analysis

## Remaining gates are estate/deployment gates, not missing portfolio implementation

- external authenticated promotion authority
- canonical estate-position resolution
- production-grade distributed nonce store
- transactional coupling to actual downstream CRM side effects
- vendor/environment adapters and organization-specific approval policy

Do not represent those external boundaries as already deployed. Do not downgrade the implemented mechanism back into a generic evaluator or scaffold.
