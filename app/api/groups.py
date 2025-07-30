from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from app.schemas import (
    GroupCreate, JoinGroupRequest,
    GroupInfo, GroupMessageCreate, GroupMessageOut
)
from app.api.auth import get_current_user
from app.db.mongodb import (
    create_group, add_user_to_group,
    get_groups_for_user, send_group_message, get_group_messages, get_group_by_id
)
from app.utils.crypto import *
from app.websockets.manager import manager

router = APIRouter(prefix="/groups", tags=["groups"])

@router.post("/", response_model=GroupInfo)
async def create_grp(data: GroupCreate, current_user: dict = Depends(get_current_user)):
    gid, key = await create_group(data.name, current_user["username"])
    return GroupInfo(id=gid, name=data.name, admin=current_user["username"], invite_key=key, members=[current_user["username"]])

@router.post("/join", response_model=dict)
async def join_grp(data: JoinGroupRequest, current_user: dict = Depends(get_current_user)):
    grp = await add_user_to_group(data.invite_key, data.username or current_user["username"], current_user["username"])
    return {"message": f"Joined {grp['name']}"}

@router.get("/", response_model=List[GroupInfo])
async def list_grps(current_user: dict = Depends(get_current_user)):
    raw = await get_groups_for_user(current_user["username"])
    return [GroupInfo(**g) for g in raw]

@router.post("/{group_id}/message", response_model=dict)
async def send_grp_msg(data: GroupMessageCreate, current_user: dict = Depends(get_current_user)):
    await send_group_message(current_user["username"], data.group_id, data.content)
    grp = await get_group_by_id(data.group_id)
    await manager.broadcast(
        grp["members"],
        {
            "type": "new_group_message",
            "data": {
                "sender": current_user["username"],
                "group_id": data.group_id,
                "content": data.content,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
    return {"message": "Sent to group"}

@router.get("/{group_id}/messages", response_model=List[GroupMessageOut])
async def list_grp_msgs(group_id: str, current_user: dict = Depends(get_current_user)):
    raw = await get_group_messages(group_id)
    return [GroupMessageOut(
        sender=m["sender"],
        content=m["content"],
        timestamp=m["timestamp"]
    ) for m in raw]