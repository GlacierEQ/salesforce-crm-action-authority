# Architecture — CRM Action Authority

This repository is an independent GlacierEQ reference implementation. It is not affiliated with Salesforce and does not claim to reproduce Salesforce internal authorization machinery.

## Recruiter layer

The mechanism solves a concrete autonomous-agent problem: an AI may understand a CRM record correctly and still be unsafe to let act on it. CRM Action Authority separates **reasoning about an action** from **authority to perform that action**.

A mutation is admitted only when a fresh external grant is bound to the exact actor, workflow subject, object family, action class, field scope, time window, and one-time nonce. Reversible mutations additionally produce a machine-readable reverse operation. External messages are treated as explicitly irreversible and remain off unless separately authorized.

## Master layer

### Decision pipeline

1. **Canonicalize inputs** — reject NaN/Inf, non-string map keys, and unsupported object types rather than coercing them.
2. **Bind identity** — actor and workflow subject must match the grant exactly.
3. **Validate authority origin** — the public leaf accepts only the declared external issuer; it does not mint its own promotion authority.
4. **Attenuate capability** — object, action, and field scopes are independently checked.
5. **Enforce time** — future grants and expired grants fail closed.
6. **Enforce single use** — a consumed nonce cannot authorize a second mutation.
7. **Classify irreversibility** — external sends require both SEND_MESSAGE scope and `allow_irreversible=true`.
8. **Construct reversal** — UPDATE restores every changed field from its before-image; DELETE recreates from its before-image; CREATE emits a delete reversal.
9. **Bind the decision** — allowed and refused decisions receive deterministic SHA-256 receipts over canonical decision inputs.

### Why the design is distinctive

The mechanism combines four ideas that are often separated:

- **Capability-style authorization:** grants are narrow, attenuated permissions rather than broad session identity.
- **Workflow provenance:** authority is tied to the workflow subject, preventing a valid grant from being borrowed by another campaign or case.
- **Reversibility as an admission requirement:** the system refuses an UPDATE or DELETE if it cannot construct a credible reverse operation before admitting the action.
- **Irreversibility as a first-class class:** sending a message is not treated as just another mutation; it requires an explicit authority bit and is labeled non-reversible in the receipt.

This creates an inspectable boundary between an agent deciding what it wants to do and a system deciding what it is permitted to do.

### Security model

| Threat | Control |
|---|---|
| Grant borrowed by another actor | exact `actor_id` binding |
| Grant reused in another workflow | exact `subject_id` binding |
| Object privilege expansion | object allowlist |
| Action privilege expansion | action allowlist |
| Field privilege expansion | object-aware field scopes |
| Expired/future capability | issuance + expiry validation |
| Replay | one-time nonce ledger |
| Hidden external send | required recipient/body/channel + irreversible flag |
| Unrecoverable update/delete | mandatory before-image |
| Ambiguous serialization | canonical JSON + fail-closed type rules |
| Leaf self-promotion | no public promotion secret; authority remains external |

### Receipt semantics

A successful reversible action returns both:

- the admitted forward action, bound into a deterministic digest; and
- a reverse-operation payload that can be persisted before side effects occur.

The reference implementation deliberately stops at the authorization boundary. It does not call a vendor API. That makes the safety property independently testable and avoids pretending a portfolio leaf has production credentials or customer access.

## Machine layer

Machine-readable surfaces:

- `machine/target-contract.json` — frozen input/invariant contract
- `machine/architecture.json` — structured mechanism graph
- `machine/verification-matrix.json` — threat-to-test mapping
- `machine/implementation-proof.json` — source-tree-bound implementation proof
- `machine/proof_receipt.json` — sanitized CI proof receipt
- `machine/operability_receipt.json` — direct-run scenario receipt
- `machine/excellence-state.json` — truthful lifecycle state

The source proof follows the estate convention: SHA-256 over sorted `src/`, `scripts/`, and `tests/` implementation-bearing files. A proof is invalid as soon as those bytes change.

## Mesh layer

The reference mechanism is complete for its portfolio boundary. Productionization would require infrastructure that intentionally remains outside this public leaf:

- durable/distributed nonce consumption instead of process-local memory;
- externally authenticated grant issuance and revocation;
- transactional coupling between receipt persistence and downstream side effects;
- vendor/API adapters with environment-specific permission verification;
- organization-specific data classification and approval policy;
- estate-level canonical-position resolution and external promotion authority.

Those are explicit deployment boundaries, not hidden claims of production completeness.
