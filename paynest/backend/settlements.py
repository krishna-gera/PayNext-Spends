from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from auth import get_current_user
from database import get_db

router = APIRouter(tags=["settlements"])


class SettlementCreate(BaseModel):
    group_id: str
    payer: str
    receiver: str
    amount: float = Field(gt=0)
    date: str


def calculate_group_balances(db: Client, group_id: str) -> Dict[str, float]:
    expenses = db.table("expenses").select("id, paid_by, amount").eq("group_id", group_id).execute().data or []
    splits = db.table("expense_splits").select("expense_id, user_id, owed_amount").eq("group_id", group_id).execute().data or []
    settlements = db.table("settlements").select("payer, receiver, amount").eq("group_id", group_id).execute().data or []

    balances: Dict[str, float] = {}
    expense_map = {e["id"]: e for e in expenses}

    for split in splits:
        user_id = split["user_id"]
        owed = float(split["owed_amount"])
        expense = expense_map.get(split["expense_id"])
        if not expense:
            continue
        payer = expense["paid_by"]

        balances[user_id] = balances.get(user_id, 0.0) - owed
        balances[payer] = balances.get(payer, 0.0) + owed

    for s in settlements:
        payer = s["payer"]
        receiver = s["receiver"]
        amount = float(s["amount"])
        balances[payer] = balances.get(payer, 0.0) + amount
        balances[receiver] = balances.get(receiver, 0.0) - amount

    return {k: round(v, 2) for k, v in balances.items()}


@router.post("/settlements")
def add_settlement(payload: SettlementCreate, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
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

    settlement = (
        db.table("settlements")
        .insert(
            {
                "group_id": payload.group_id,
                "payer": payload.payer,
                "receiver": payload.receiver,
                "amount": payload.amount,
                "date": payload.date,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    return settlement.data[0]


@router.get("/balances/{group_id}")
def get_balances(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    membership = (
        db.table("group_members").select("*").eq("group_id", group_id).eq("user_id", current_user["id"]).limit(1).execute()
    )
    if not membership.data:
        raise HTTPException(status_code=403, detail="No group access")
    return calculate_group_balances(db, group_id)
