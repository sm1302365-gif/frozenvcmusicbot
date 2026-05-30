"""Subscription / plan routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from kwaicut.backend.dependencies import get_current_user
from kwaicut.backend.schemas import SubscriptionOut
from kwaicut.db.base import get_db
from kwaicut.db.models import PlanTier, Subscription, User

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

# Plan entitlements consumed by the UI and enforced server-side.
PLAN_LIMITS: dict[PlanTier, dict] = {
    PlanTier.FREE: {"ai_credits": 100, "cloud_storage_bytes": 1_073_741_824, "max_export": "720p"},
    PlanTier.PREMIUM: {"ai_credits": -1, "cloud_storage_bytes": -1, "max_export": "8k"},
    PlanTier.ENTERPRISE: {"ai_credits": -1, "cloud_storage_bytes": -1, "max_export": "8k"},
}


@router.get("", response_model=SubscriptionOut)
def get_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return user.subscription


@router.post("/upgrade", response_model=SubscriptionOut)
def upgrade(
    tier: PlanTier,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Switch the user's plan and apply that tier's entitlements.

    A real deployment would gate this behind a verified payment webhook; here it
    updates entitlements directly so the flow is demoable end-to-end.
    """
    sub: Subscription = user.subscription
    if sub is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no subscription on file")
    limits = PLAN_LIMITS[tier]
    sub.tier = tier
    sub.ai_credits = 1_000_000 if limits["ai_credits"] == -1 else limits["ai_credits"]
    sub.cloud_storage_bytes = (
        1_099_511_627_776 if limits["cloud_storage_bytes"] == -1 else limits["cloud_storage_bytes"]
    )
    db.flush()
    return sub
