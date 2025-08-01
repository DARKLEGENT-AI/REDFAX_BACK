from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import (
    GroupCreate, JoinGroupRequest,
    GroupInfo, GroupMessageCreate, GroupMessageOut)
from app.api.auth import get_current_user
from app.db.mongodb import (
    create_group, add_user_to_group,
    get_groups_for_user, get_group_by_id)
from app.utils.crypto import *
from app.websockets.manager import manager
from app.schemas import *
from app.api.auth import *
from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter, Query
from app.db.mongodb import db

router = APIRouter(prefix="/groups", tags=["groups"])

### ГРУППЫ ###

@router.post("/")
async def create_group_endpoint(
    group: GroupCreate,
    current_user: dict = Depends(get_current_user)
):
    group_id, invite_key = await create_group(group.name, current_user["username"])
    return {"group_id": group_id, "invite_key": invite_key}

@router.post("/join")
async def join_group_endpoint(
    request: JoinGroupRequest,
    current_user: dict = Depends(get_current_user)
):
    username = request.username or current_user["username"]
    group = await add_user_to_group(request.invite_key, username, current_user["username"])
    return {"message": f"{username} added to group {group['name']}"}

@router.delete("/{group_id}")
async def delete_group_endpoint(
    group_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Проверка, есть ли такая группа и текущий пользователь — её создатель
    group = await get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    if group["creator"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Только создатель может удалить группу")

    # Удаляем группу
    await db.groups.delete_one({"_id": ObjectId(group_id)})

    # Удаляем все сообщения, связанные с этой группой
    delete_result = await db.group_messages.delete_many({"group_id": group_id})

    return {
        "message": "Group and related messages deleted successfully",
        "deleted_messages_count": delete_result.deleted_count
    }

@router.get("/", response_model=List[GroupInfo])
async def list_user_groups(current_user: dict = Depends(get_current_user)):
    groups = await get_groups_for_user(current_user["username"])
    return groups

@router.get("/messages", response_model=List[MessageOut])
async def get_group_messages(
    group_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    # Проверка существования группы
    group = await get_group_by_id(group_id)
    if not group:
        raise HTTPException(404, detail="Группа не найдена")

    # Проверка членства пользователя
    if current_user["username"] not in group["members"]:
        raise HTTPException(403, detail="Вы не состоите в этой группе")

    # Получаем все сообщения этой группы
    cursor = db.group_messages.find({"group_id": group_id}).sort("timestamp", 1)

    messages = []
    async for msg in cursor:
        audio_url = None
        file_url = None
        filename = None
        file_id = msg.get("file_id")

        if msg.get("audio_file_id"):
            audio_url = f"/voice/{msg['audio_file_id']}"

        if file_id:
            file_url = f"/file/{file_id}"
            try:
                file_doc = await db.fs.files.find_one({"_id": ObjectId(file_id)})
                if file_doc:
                    filename = file_doc["filename"]
            except:
                pass

        messages.append(MessageOut(
            sender=msg["sender"],
            receiver=group_id,  # в этом случае "receiver" — это id группы
            content=decrypt_message(msg["content"]) if msg.get("content") else None,
            audio_url=audio_url,
            file_id=str(file_id) if file_id else None,
            file_url=file_url,
            filename=filename,
            timestamp=msg["timestamp"]
        ))

    return messages
