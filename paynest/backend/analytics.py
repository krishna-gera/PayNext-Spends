from collections import defaultdict
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from auth import get_current_user
from database import get_db

router = APIRouter(tags=["analytics"])


@router.get("/analytics/{group_id}")
def get_analytics(group_id: str, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    membership = (
        db.table("group_members").select("*").eq("group_id", group_id).eq("user_id", current_user["id"]).limit(1).execute()
    )
    if not membership.data:
        raise HTTPException(status_code=403, detail="No group access")

    expenses = db.table("expenses").select("amount, paid_by, date, title").eq("group_id", group_id).execute().data or []

    by_user = defaultdict(float)
    by_category = defaultdict(float)
    by_month = defaultdict(float)

    for row in expenses:
        amount = float(row["amount"])
        by_user[row["paid_by"]] += amount

        category = (row.get("title") or "other").split(" ")[0].lower()
        by_category[category] += amount

        dt = datetime.fromisoformat(row["date"])
        by_month[dt.strftime("%Y-%m")] += amount

    return {
        "who_spent_most": by_user,
        "category_spending": by_category,
        "monthly_spending": by_month,
    }
