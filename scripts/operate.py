#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crm_action_authority import (  # noqa: E402
    Action,
    ActionGrant,
    CrmActionAuthority,
    CrmActionAuthorityRequest,
    Decision,
)


def main() -> int:
    authority = CrmActionAuthority()

    update_grant = ActionGrant(
        grant_id="operate-update",
        issuer="external-crm-action-authority",
        actor_id="campaign-agent",
        subject_id="sandbox-campaign",
        object_types=("Lead",),
        actions=(Action.UPDATE,),
        field_scopes=("Lead.Status",),
        issued_at=100.0,
        not_after=200.0,
        nonce="operate-update-1",
    )
    allowed_update = authority.evaluate(
        CrmActionAuthorityRequest(
            actor_id="campaign-agent",
            subject_id="sandbox-campaign",
            object_type="Lead",
            action=Action.UPDATE,
            record_id="lead-1",
            changes={"Status": "Qualified"},
            before={"Status": "Open"},
            grant=update_grant,
            now=150.0,
        )
    )

    blocked_send = authority.evaluate(
        CrmActionAuthorityRequest(
            actor_id="campaign-agent",
            subject_id="sandbox-campaign",
            object_type="Lead",
            action=Action.SEND_MESSAGE,
            record_id="lead-1",
            changes={"recipient": "person@example.test", "body": "Hello", "channel": "email"},
            before={},
            grant=None,
            now=150.0,
        )
    )

    send_grant = ActionGrant(
        grant_id="operate-send",
        issuer="external-crm-action-authority",
        actor_id="campaign-agent",
        subject_id="sandbox-campaign",
        object_types=("Lead",),
        actions=(Action.SEND_MESSAGE,),
        field_scopes=("Lead.recipient", "Lead.body", "Lead.channel"),
        issued_at=100.0,
        not_after=200.0,
        nonce="operate-send-1",
        allow_irreversible=True,
    )
    allowed_send = authority.evaluate(
        CrmActionAuthorityRequest(
            actor_id="campaign-agent",
            subject_id="sandbox-campaign",
            object_type="Lead",
            action=Action.SEND_MESSAGE,
            record_id="lead-1",
            changes={"recipient": "person@example.test", "body": "Hello", "channel": "email"},
            before={},
            grant=send_grant,
            now=150.0,
        )
    )

    if allowed_update.decision is not Decision.ALLOW:
        raise SystemExit("expected scoped update to be allowed")
    if blocked_send.decision is not Decision.REFUSE:
        raise SystemExit("external send must default to refused")
    if allowed_send.decision is not Decision.ALLOW:
        raise SystemExit("explicitly authorized send should be allowed")
    if allowed_update.reverse_operation.get("changes") != {"Status": "Open"}:
        raise SystemExit("update reverse receipt did not bind before image")

    print(
        json.dumps(
            {
                "status": "PASS",
                "update": allowed_update.as_dict(),
                "no_send_default": blocked_send.as_dict(),
                "authorized_send": allowed_send.as_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
