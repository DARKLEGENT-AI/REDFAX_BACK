from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas import FriendAddRequest, FriendListResponse, FriendInfo
from app.api.auth import get_current_user
from app.db.mongodb import get_user, add_friend_db, get_friends

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/add", response_model=dict)
async def add_friend(req: FriendAddRequest, current_user: dict = Depends(get_current_user)):
    me = current_user["username"]
    if req.username == me:
        raise HTTPException(400, "Cannot add yourself")
    if not await get_user(req.username):
        raise HTTPException(404, "User not found")
    await add_friend_db(me, req.username)
    await add_friend_db(req.username, me)
    return {"message": f"{req.username} is now friend"}

@router.get("/list", response_model=FriendListResponse)
async def list_friends(current_user: dict = Depends(get_current_user)):
    lst = await get_friends(current_user["username"])
    return FriendListResponse(friends=[FriendInfo(username=u) for u in lst])