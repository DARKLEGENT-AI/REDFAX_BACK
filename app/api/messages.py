from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List

from app.schemas import MessagePayload, MessageOut
from app.api.auth import get_current_user
from app.db.mongodb import create_message, get_messages_for_user
from app.utils.crypto import encrypt_message, decrypt_message
from app.websockets.manager import manager

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=dict)
async def send_message(payload: MessagePayload, current_user: dict = Depends(get_current_user)):
    if not payload.content:
        raise HTTPException(400, "Empty content")
    encrypted = encrypt_message(payload.content)
    await create_message(
        sender=current_user["username"],
        receiver=payload.receiver,
        content=encrypted,
        audio_file_id=None,
        file_id=None
    )
    # WS‑уведомление
    await manager.send_personal(
        payload.receiver,
        {
            "type": "new_message",
            "data": {
                "sender": current_user["username"],
                "receiver": payload.receiver,
                "content": payload.content,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
    return {"message": "Sent"}

@router.get("/", response_model=List[MessageOut])
async def list_messages(current_user: dict = Depends(get_current_user)):
    raw = await get_messages_for_user(current_user["username"])
    out = []
    for m in raw:
        out.append(MessageOut(
            sender=m["sender"],
            receiver=m["receiver"],
            content=decrypt_message(m["content"]) if m.get("content") else None,
            audio_url=None,
            file_id=str(m.get("file_id")) if m.get("file_id") else None,
            file_url=None,
            filename=None,
            timestamp=m["timestamp"]
        ))
    return out