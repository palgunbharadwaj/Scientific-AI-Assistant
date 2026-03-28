from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from backend.auth import get_current_user, require_role
from backend.models import (
    TokenData, UserRole, PendingApproval, ApprovalDecision, QueryResponse
)
from backend.services.audit_logger import log_event

router = APIRouter(prefix="/admin", tags=["Admin"])

# In-memory pending approvals store (replace with DB in production)
_pending_store: dict[str, PendingApproval] = {}


def add_pending_approval(approval: PendingApproval):
    """Called by the orchestrator when a high-risk result is flagged."""
    _pending_store[approval.approval_id] = approval


@router.get("/pending", response_model=List[PendingApproval])
async def get_pending_approvals(
    current_user: TokenData = Depends(require_role(UserRole.admin))
):
    """List all high-risk outputs awaiting admin review."""
    return list(_pending_store.values())


@router.post("/decide", response_model=dict)
async def decide_approval(
    decision: ApprovalDecision,
    current_user: TokenData = Depends(require_role(UserRole.admin))
):
    """Admin approves or rejects a flagged high-risk output."""
    if decision.approval_id not in _pending_store:
        raise HTTPException(status_code=404, detail="Approval request not found")

    item = _pending_store.pop(decision.approval_id)
    action = "APPROVED" if decision.approved else "REJECTED"

    log_event(
        event_type=f"ADMIN_{action}",
        user=current_user.username,
        details={
            "approval_id": decision.approval_id,
            "query": item.query,
            "agent": item.agent,
            "note": decision.admin_note,
        },
    )

    return {
        "status": action,
        "approval_id": decision.approval_id,
        "note": decision.admin_note,
    }
