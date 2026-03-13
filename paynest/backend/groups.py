from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from supabase import Client

from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    name: str
    currency: str = "INR"


class AddMemberRequest(BaseModel):
    group_id: str
    email: EmailStr
    role: str = "member"


@router.get("")
def get_groups(current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)) -> List[Dict[str, Any]]:
    membership = db.table("group_members").select("group_id").eq("user_id", current_user["id"]).execute()
    group_ids = [row["group_id"] for row in membership.data or []]
    if not group_ids:
        return []
    groups = db.table("groups").select("*").in_("id", group_ids).order("created_at", desc=True).execute()
    return groups.data or []


@router.post("")
def create_group(payload: CreateGroupRequest, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    group = (
        db.table("groups")
        .insert(
            {
                "name": payload.name,
                "created_by": current_user["id"],
                "currency": payload.currency,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    group_id = group.data[0]["id"]
    db.table("group_members").insert(
        {
            "group_id": group_id,
            "user_id": current_user["id"],
            "role": "owner",
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()
    return group.data[0]


@router.post("/add-member")
def add_member(payload: AddMemberRequest, current_user: Dict[str, Any] = Depends(get_current_user), db: Client = Depends(get_db)):
    owner_check = (
        db.table("group_members")
        .select("*")
        .eq("group_id", payload.group_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not owner_check.data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a group member")

    user = db.table("users").select("*").eq("email", payload.email).limit(1).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    target = user.data[0]
    existing = (
        db.table("group_members")
        .select("*")
        .eq("group_id", payload.group_id)
        .eq("user_id", target["id"])
        .limit(1)
        .execute()
    )
    if existing.data:
        return {"message": "User already in group"}

    inserted = (
        db.table("group_members")
        .insert(
            {
                "group_id": payload.group_id,
                "user_id": target["id"],
                "role": payload.role,
                "joined_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )
    return inserted.data[0]
