from __future__ import annotations

import math

from crm_action_authority import (
    Action,
    ActionGrant,
    CrmActionAuthority,
    CrmActionAuthorityRequest,
    Decision,
)


def make_grant(**overrides):
    data = dict(
        grant_id="g-adv",
        issuer="external-crm-action-authority",
        actor_id="agent-1",
        subject_id="case-1",
        object_types=("Contact",),
        actions=(Action.UPDATE,),
        field_scopes=("Contact.Email",),
        issued_at=10.0,
        not_after=20.0,
        nonce="adv-1",
        allow_irreversible=False,
    )
    data.update(overrides)
    return ActionGrant(**data)


def make_req(**overrides):
    data = dict(
        actor_id="agent-1",
        subject_id="case-1",
        object_type="Contact",
        action=Action.UPDATE,
        record_id="c-1",
        changes={"Email": "new@example.test"},
        before={"Email": "old@example.test"},
        grant=make_grant(),
        now=15.0,
    )
    data.update(overrides)
    return CrmActionAuthorityRequest(**data)


def assert_refused(**overrides):
    receipt = CrmActionAuthority().evaluate(make_req(**overrides))
    assert receipt.decision is Decision.REFUSE
    return receipt


def test_wrong_actor_cannot_borrow_grant():
    assert "grant_actor_mismatch" in assert_refused(actor_id="agent-2").reasons


def test_wrong_subject_cannot_borrow_grant():
    assert "grant_subject_mismatch" in assert_refused(subject_id="case-2").reasons


def test_wrong_object_cannot_borrow_grant():
    assert "grant_object_scope_missing" in assert_refused(object_type="Account").reasons


def test_wrong_action_cannot_borrow_grant():
    assert "grant_action_scope_missing" in assert_refused(action=Action.DELETE).reasons


def test_expired_grant_fails_closed():
    assert "grant_expired" in assert_refused(now=21.0).reasons


def test_future_grant_fails_closed():
    assert "grant_not_active" in assert_refused(now=9.0).reasons


def test_non_finite_payload_is_rejected():
    receipt = assert_refused(changes={"Email": math.nan}, before={"Email": "old@example.test"})
    assert "non_canonical_payload" in receipt.reasons


def test_delete_requires_before_image_and_explicit_delete_scope():
    delete_grant = make_grant(
        actions=(Action.DELETE,),
        field_scopes=("*",),
        nonce="delete-1",
    )
    receipt = CrmActionAuthority().evaluate(
        make_req(action=Action.DELETE, changes={}, before={}, grant=delete_grant)
    )
    assert receipt.decision is Decision.REFUSE
    assert "before_image_required_for_delete" in receipt.reasons


def test_send_cannot_hide_missing_recipient():
    send_grant = make_grant(
        actions=(Action.SEND_MESSAGE,),
        field_scopes=("*",),
        allow_irreversible=True,
        nonce="send-adv",
    )
    receipt = CrmActionAuthority().evaluate(
        make_req(
            action=Action.SEND_MESSAGE,
            changes={"body": "Hello", "channel": "email"},
            before={},
            grant=send_grant,
        )
    )
    assert receipt.decision is Decision.REFUSE
    assert receipt.reasons[0].startswith("send_fields_missing")


def test_wrong_issuer_fails_closed():
    receipt = assert_refused(grant=make_grant(issuer="leaf-local-signer"))
    assert "grant_issuer_mismatch" in receipt.reasons
