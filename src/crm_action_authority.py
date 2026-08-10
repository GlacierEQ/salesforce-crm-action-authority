"""CRM Action Authority — deterministic fail-closed CRM mutation authorization.

Independent GlacierEQ reference implementation aligned to CRM agent governance themes.
No Salesforce affiliation, proprietary access, or production deployment is claimed.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ContractError(ValueError):
    """Raised when an input cannot participate in the authority contract."""


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"


class Action(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SEND_MESSAGE = "SEND_MESSAGE"


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractError("non-finite numbers are not canonical")
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ContractError("canonical object keys must be strings")
        return {key: _normalize(value[key]) for key in sorted(value)}
    raise ContractError(f"unsupported canonical type: {type(value).__name__}")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ActionGrant:
    grant_id: str
    issuer: str
    actor_id: str
    subject_id: str
    object_types: tuple[str, ...]
    actions: tuple[Action, ...]
    field_scopes: tuple[str, ...]
    issued_at: float
    not_after: float
    nonce: str
    allow_irreversible: bool = False

    def validate_times(self, now: float) -> None:
        for label, value in (
            ("issued_at", self.issued_at),
            ("not_after", self.not_after),
            ("now", now),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ContractError(f"{label} must be numeric")
            if not math.isfinite(float(value)):
                raise ContractError(f"{label} must be finite")
        if self.not_after <= self.issued_at:
            raise ContractError("grant lifetime invalid")
        if now < self.issued_at:
            raise ContractError("grant not active")
        if now > self.not_after:
            raise ContractError("grant expired")


@dataclass(frozen=True)
class CrmActionAuthorityRequest:
    actor_id: str
    subject_id: str
    object_type: str
    action: Action
    record_id: str | None
    changes: dict[str, Any] = field(default_factory=dict)
    before: dict[str, Any] = field(default_factory=dict)
    grant: ActionGrant | None = None
    now: float = 0.0


@dataclass(frozen=True)
class CrmActionAuthorityReceipt:
    decision: Decision
    reasons: tuple[str, ...]
    digest: str
    action: Action
    object_type: str
    record_id: str | None
    authorized_fields: tuple[str, ...] = ()
    reverse_operation: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reasons": list(self.reasons),
            "digest": self.digest,
            "action": self.action.value,
            "object_type": self.object_type,
            "record_id": self.record_id,
            "authorized_fields": list(self.authorized_fields),
            "reverse_operation": self.reverse_operation,
            "metrics": self.metrics,
        }


class CrmActionAuthority:
    """Authorize CRM mutations only when a fresh, scoped one-time grant permits them."""

    REQUIRED_ISSUER = "external-crm-action-authority"

    def __init__(self) -> None:
        self._consumed_nonces: set[str] = set()

    @staticmethod
    def _field_allowed(object_type: str, field_name: str, scopes: tuple[str, ...]) -> bool:
        accepted = {
            "*",
            f"{object_type}.*",
            field_name,
            f"{object_type}.{field_name}",
        }
        return any(scope in accepted for scope in scopes)

    @staticmethod
    def _reverse_operation(req: CrmActionAuthorityRequest) -> dict[str, Any]:
        if req.action is Action.CREATE:
            return {
                "reversible": True,
                "action": Action.DELETE.value,
                "object_type": req.object_type,
                "record_id": req.record_id,
            }
        if req.action is Action.UPDATE:
            restore: dict[str, Any] = {}
            for field_name in sorted(req.changes):
                if field_name not in req.before:
                    raise ContractError(f"before image missing for field: {field_name}")
                restore[field_name] = req.before[field_name]
            return {
                "reversible": True,
                "action": Action.UPDATE.value,
                "object_type": req.object_type,
                "record_id": req.record_id,
                "changes": restore,
            }
        if req.action is Action.DELETE:
            if not req.before:
                raise ContractError("before image required for delete")
            return {
                "reversible": True,
                "action": Action.CREATE.value,
                "object_type": req.object_type,
                "record_id": req.record_id,
                "changes": req.before,
            }
        return {
            "reversible": False,
            "action": "NONE",
            "reason": "external_send_has_no_automatic_reverse",
        }

    def _refuse(self, req: CrmActionAuthorityRequest, *reasons: str) -> CrmActionAuthorityReceipt:
        try:
            changes_fingerprint = _digest(req.changes)
        except ContractError:
            changes_fingerprint = "NON_CANONICAL"
        try:
            before_fingerprint = _digest(req.before)
        except ContractError:
            before_fingerprint = "NON_CANONICAL"
        body = {
            "decision": Decision.REFUSE,
            "actor_id": req.actor_id,
            "subject_id": req.subject_id,
            "object_type": req.object_type,
            "action": req.action,
            "record_id": req.record_id,
            "changes_fingerprint": changes_fingerprint,
            "before_fingerprint": before_fingerprint,
            "reasons": reasons,
        }
        return CrmActionAuthorityReceipt(
            decision=Decision.REFUSE,
            reasons=tuple(reasons),
            digest=_digest(body),
            action=req.action,
            object_type=req.object_type,
            record_id=req.record_id,
            metrics={"grant_consumed": False, "field_count": len(req.changes)},
        )

    def evaluate(self, req: CrmActionAuthorityRequest) -> CrmActionAuthorityReceipt:
        if not req.actor_id.strip():
            return self._refuse(req, "actor_id_missing")
        if not req.subject_id.strip():
            return self._refuse(req, "subject_id_missing")
        if not req.object_type.strip():
            return self._refuse(req, "object_type_missing")
        if req.action in {Action.UPDATE, Action.DELETE, Action.SEND_MESSAGE} and not (
            req.record_id and req.record_id.strip()
        ):
            return self._refuse(req, "record_id_missing")

        try:
            _normalize(req.changes)
            _normalize(req.before)
        except ContractError:
            return self._refuse(req, "non_canonical_payload")

        grant = req.grant
        if grant is None:
            return self._refuse(req, "grant_missing")
        if not grant.grant_id.strip() or not grant.nonce.strip():
            return self._refuse(req, "grant_identity_missing")
        if grant.issuer != self.REQUIRED_ISSUER:
            return self._refuse(req, "grant_issuer_mismatch")
        if grant.actor_id != req.actor_id:
            return self._refuse(req, "grant_actor_mismatch")
        if grant.subject_id != req.subject_id:
            return self._refuse(req, "grant_subject_mismatch")
        if req.object_type not in grant.object_types and "*" not in grant.object_types:
            return self._refuse(req, "grant_object_scope_missing")
        if req.action not in grant.actions:
            return self._refuse(req, "grant_action_scope_missing")
        try:
            grant.validate_times(req.now)
        except ContractError as exc:
            return self._refuse(req, str(exc).replace(" ", "_"))
        if grant.nonce in self._consumed_nonces:
            return self._refuse(req, "grant_replay")

        fields = tuple(sorted(req.changes))
        denied_fields = [
            name
            for name in fields
            if not self._field_allowed(req.object_type, name, grant.field_scopes)
        ]
        if denied_fields:
            return self._refuse(req, "grant_field_scope_missing:" + ",".join(denied_fields))

        if req.action is Action.SEND_MESSAGE:
            required = {"recipient", "body", "channel"}
            missing = sorted(required.difference(req.changes))
            if missing:
                return self._refuse(req, "send_fields_missing:" + ",".join(missing))
            if not grant.allow_irreversible:
                return self._refuse(req, "irreversible_action_not_authorized")

        try:
            reverse = self._reverse_operation(req)
        except ContractError as exc:
            return self._refuse(req, str(exc).replace(" ", "_"))

        body = {
            "decision": Decision.ALLOW,
            "grant_id": grant.grant_id,
            "nonce": grant.nonce,
            "actor_id": req.actor_id,
            "subject_id": req.subject_id,
            "object_type": req.object_type,
            "action": req.action,
            "record_id": req.record_id,
            "changes": req.changes,
            "before": req.before,
            "authorized_fields": fields,
            "reverse_operation": reverse,
        }
        receipt = CrmActionAuthorityReceipt(
            decision=Decision.ALLOW,
            reasons=("grant_valid",),
            digest=_digest(body),
            action=req.action,
            object_type=req.object_type,
            record_id=req.record_id,
            authorized_fields=fields,
            reverse_operation=reverse,
            metrics={
                "grant_consumed": True,
                "field_count": len(fields),
                "reversible": reverse["reversible"],
            },
        )
        self._consumed_nonces.add(grant.nonce)
        return receipt


Mechanism = CrmActionAuthority
