from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from auth import get_current_user
from database import get_db

router = APIRouter(tags=["expenses"])


SplitType = Literal["equal", "percentage", "exact", "share"]


class ParticipantShare(BaseModel):
    user_id: str
    value: float = Field(gt=0)


class ExpenseCreate(BaseModel):
    group_id: str
    title: str
    amount: float = Field(gt=0)
    paid_by: str
    date: str
    description: str = ""
    receipt_url: str | None = None
    split_type: SplitType = "equal"
    participants: List[ParticipantShare]


def compute_portions(amount: float, split_type: SplitType, participants: List[ParticipantShare]) -> Dict[str, float]:
    if not participants:
        raise HTTPException(status_code=400, detail="Participants required")

    if split_type == "equal":
        value = round(amount / len(participants), 2)
        return {p.user_id: value for p in participants}

    total = sum(p.value for p in participants)
    if total <= 0:
        raise HTTPException(status_code=400, detail="Invalid split values")

    if split_type == "percentage":
        if round(total, 2) != 100:
            raise HTTPException(status_code=400, detail="Percentages must sum to 100")
        return {p.user_id: round(amount * (p.value / 100), 2) for p in participants}

    if split_type == "exact":
        if round(total, 2) != round(amount, 2):
            raise HTTPException(status_code=400, detail="Exact amounts must equal total")
        return {p.user_id: round(p.value, 2) for p in participants}

    return {p.user_id: round(amount * (p.value / total), 2) for p in participants}


@router.post("/expenses")
def add_expense(payload: ExpenseCreate, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    membership = (
        db.table("group_members")
        .select("*")
        .eq("group_id", payload.group_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not membership.data:
        raise HTTPException(status_code=403, detail="No group access")

    expense = (
        db.table("expenses")
        .insert(
            {
                "group_id": payload.group_id,
                "title": payload.title,
                "amount": payload.amount,
                "paid_by": payload.paid_by,
                "date": payload.date,
                "description": payload.description,
                "receipt_url": payload.receipt_url,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    expense_id = expense.data[0]["id"]

    portions = compute_portions(payload.amount, payload.split_type, payload.participants)
    rows = [
        {
            "expense_id": expense_id,
            "group_id": payload.group_id,
            "user_id": user_id,
            "owed_amount": amount,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for user_id, amount in portions.items()
    ]
    db.table("expense_splits").insert(rows).execute()
    return {"expense": expense.data[0], "splits": rows}


@router.get("/expenses/{group_id}")
def get_expenses(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    membership = (
        db.table("group_members").select("*").eq("group_id", group_id).eq("user_id", current_user["id"]).limit(1).execute()
    )
    if not membership.data:
        raise HTTPException(status_code=403, detail="No group access")

    expenses = db.table("expenses").select("*").eq("group_id", group_id).order("date", desc=True).execute()
    return expenses.data or []
