from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas import FriendAddRequest, FriendListResponse, FriendInfo
from app.api.auth import get_current_user
from app.db.mongodb import get_user, add_friend_db, get_friends

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/add", response_model=dict)
async def add_friend(req: FriendAddRequest, current_user: dict = Depends(get_current_user)):
    if req.username == current_user["username"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself")

    friend = await get_user(req.username)
    if not friend:
        raise HTTPException(status_code=404, detail="User not found")

    # Добавляем друга в список текущего пользователя
    await add_friend_db(current_user["username"], req.username)

    # Добавляем текущего пользователя в список друга
    await add_friend_db(req.username, current_user["username"])

    return {"message": f"{req.username} added as friend (mutual)"}

@router.get("/list", response_model=FriendListResponse)
async def list_friends(current_user: dict = Depends(get_current_user)):
    friends = await get_friends(current_user["username"])
    return FriendListResponse(friends=[FriendInfo(username=f) for f in friends])