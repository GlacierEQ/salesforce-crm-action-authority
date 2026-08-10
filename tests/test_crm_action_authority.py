from __future__ import annotations

from crm_action_authority import (
    Action,
    ActionGrant,
    CrmActionAuthority,
    CrmActionAuthorityRequest,
    Decision,
)


def grant(**overrides):
    data = dict(
        grant_id="g-1",
        issuer="external-crm-action-authority",
        actor_id="agent-7",
        subject_id="campaign-1",
        object_types=("Lead",),
        actions=(Action.UPDATE,),
        field_scopes=("Lead.Status", "Lead.OwnerId"),
        issued_at=100.0,
        not_after=200.0,
        nonce="nonce-1",
        allow_irreversible=False,
    )
    data.update(overrides)
    return ActionGrant(**data)


def request(**overrides):
    data = dict(
        actor_id="agent-7",
        subject_id="campaign-1",
        object_type="Lead",
        action=Action.UPDATE,
        record_id="lead-42",
        changes={"Status": "Qualified"},
        before={"Status": "Open"},
        grant=grant(),
        now=150.0,
    )
    data.update(overrides)
    return CrmActionAuthorityRequest(**data)


def test_scoped_update_allowed_and_reverse_receipt_restores_before_image():
    receipt = CrmActionAuthority().evaluate(request())
    assert receipt.decision is Decision.ALLOW
    assert receipt.authorized_fields == ("Status",)
    assert receipt.reverse_operation == {
        "reversible": True,
        "action": "UPDATE",
        "object_type": "Lead",
        "record_id": "lead-42",
        "changes": {"Status": "Open"},
    }
    assert receipt.metrics["grant_consumed"] is True


def test_missing_grant_refuses():
    receipt = CrmActionAuthority().evaluate(request(grant=None))
    assert receipt.decision is Decision.REFUSE
    assert "grant_missing" in receipt.reasons


def test_field_outside_grant_refuses():
    receipt = CrmActionAuthority().evaluate(
        request(changes={"AnnualRevenue": 10_000}, before={"AnnualRevenue": 9000})
    )
    assert receipt.decision is Decision.REFUSE
    assert receipt.reasons[0].startswith("grant_field_scope_missing")


def test_update_without_before_image_refuses_because_reverse_is_not_constructible():
    receipt = CrmActionAuthority().evaluate(request(before={}))
    assert receipt.decision is Decision.REFUSE
    assert "before_image_missing_for_field:_Status" in receipt.reasons


def test_grant_nonce_is_one_time():
    authority = CrmActionAuthority()
    first = authority.evaluate(request())
    second = authority.evaluate(request())
    assert first.decision is Decision.ALLOW
    assert second.decision is Decision.REFUSE
    assert "grant_replay" in second.reasons


def test_external_send_requires_explicit_irreversible_authority():
    send_grant = grant(
        actions=(Action.SEND_MESSAGE,),
        field_scopes=("Lead.recipient", "Lead.body", "Lead.channel"),
        nonce="send-1",
        allow_irreversible=False,
    )
    req = request(
        action=Action.SEND_MESSAGE,
        changes={"recipient": "person@example.test", "body": "Hello", "channel": "email"},
        before={},
        grant=send_grant,
    )
    receipt = CrmActionAuthority().evaluate(req)
    assert receipt.decision is Decision.REFUSE
    assert "irreversible_action_not_authorized" in receipt.reasons


def test_external_send_with_explicit_scope_and_irreversible_flag_is_allowed():
    send_grant = grant(
        actions=(Action.SEND_MESSAGE,),
        field_scopes=("Lead.recipient", "Lead.body", "Lead.channel"),
        nonce="send-2",
        allow_irreversible=True,
    )
    req = request(
        action=Action.SEND_MESSAGE,
        changes={"recipient": "person@example.test", "body": "Hello", "channel": "email"},
        before={},
        grant=send_grant,
    )
    receipt = CrmActionAuthority().evaluate(req)
    assert receipt.decision is Decision.ALLOW
    assert receipt.reverse_operation["reversible"] is False


def test_different_changes_bind_different_receipt_digests():
    first = CrmActionAuthority().evaluate(request())
    second = CrmActionAuthority().evaluate(
        request(
            changes={"Status": "Working"},
            before={"Status": "Open"},
            grant=grant(nonce="nonce-2"),
        )
    )
    assert first.digest != second.digest
