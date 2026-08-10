# Engineering Handoff — CRM Action Authority

The core CRM action-authority mechanism is implemented. This document defines the remaining proof and integration work without changing the truth boundary.

## Implemented now

- deterministic canonical payload binding
- actor / subject / object / action grant scoping
- field-level mutation scopes
- issuance, expiry, and one-time nonce enforcement
- update/delete before-image requirements
- reverse-operation receipts for reversible mutations
- no-send default for external messaging
- explicit irreversible authorization for `SEND_MESSAGE`
- fail-closed handling of unsupported and non-finite payload values
- direct operate surface plus behavioral and adversarial tests

## Invariants to preserve

1. A public leaf must never mint its own promotion authority.
2. External messaging must never become an implicit side effect of a CRM update.
3. A field omitted from the grant is not writable.
4. A consumed nonce is never reusable.
5. UPDATE and DELETE cannot be admitted if the reverse operation cannot be reconstructed.
6. Unsupported payload types must fail closed; never restore `json.dumps(..., default=str)`.
7. The repository must remain explicit about its independent, non-affiliated status.

## Next proof gate

Generate `machine/implementation-proof.json` only from the current merged source head, after the repository workflow proves:

- behavioral cases >= 3
- adversarial cases >= 1
- direct `scripts/operate.py` success
- no remaining implementation-placeholder markers
- exact repository/source binding

That receipt may make the implementation eligible for the Helix promotion assessment, but does not itself grant promotion authority.

## External integration gate

A real promotion/signing service should inject authority claims from outside this repository. The public repository may verify claims, but must not contain the production signing secret.
