from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List
from app.schemas import MessagePayload, MessageOut
from app.api.auth import get_current_user
from app.db.mongodb import *
from app.utils.crypto import encrypt_message, decrypt_message
from app.websockets.endpoint import push_personal_message
from app.options import MAX_MESSAGE_LENGTH
from typing import List
from fastapi.responses import JSONResponse
from app.schemas import *
from app.api.auth import *
from bson import ObjectId
from fastapi import UploadFile, File, Depends, HTTPException, APIRouter, Form

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/send", response_model=dict)
async def send_message(
    payload: MessagePayload,
    current_user: dict = Depends(get_current_user)
):
    receiver = payload.receiver
    content = payload.content

    # проверяем длину сообщения
    if len(content) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Длина сообщения не должна превышать {MAX_MESSAGE_LENGTH} символов"
        )

    # … ваши остальные валидации …

    # шифруем и сохраняем
    encrypted_content = encrypt_message(content)
    await create_message(
        sender=current_user["username"],
        receiver=receiver,
        content=encrypted_content,
        audio_file_id=None
    )

    # формируем данные для клиента и пушим через WS
    message_data = {
        "sender": current_user["username"],
        "receiver": receiver,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    payload_ws = {
        "type": "new_message",
        "data": message_data
    }
    await push_personal_message(receiver, payload_ws)

    return JSONResponse({"message": "Сообщение отправлено"}, status_code=201)

@router.post("/send/voice")
async def send_voice_message(
    receiver: str = Form(None),
    group_id: str = Form(None),
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # … ваши валидации и загрузка в GridFS …
    contents = await audio_file.read()
    file_id = await voice_fs_bucket.upload_from_stream(
        audio_file.filename, contents,
        metadata={"user_id": current_user["username"], "type": "voice"}
    )
    audio_file_id = str(file_id)

    if receiver:
        # личка
        await create_message(
            sender=current_user["username"],
            receiver=receiver,
            content=None,
            audio_file_id=audio_file_id
        )
        message_data = {
            "sender": current_user["username"],
            "receiver": receiver,
            "audio_url": f"/voice/{audio_file_id}",
            "timestamp": datetime.utcnow().isoformat()
        }
        payload_ws = {"type": "new_voice_message", "data": message_data}
        await push_personal_message(receiver, payload_ws)
        return JSONResponse({"message": "Голосовое сообщение отправлено"}, status_code=201)

    # группа
    group = await get_group_by_id(group_id)
    await db.group_messages.insert_one({
        "group_id": group_id,
        "sender": current_user["username"],
        "audio_file_id": audio_file_id,
        "timestamp": datetime.utcnow()
    })
    message_data = {
        "sender": current_user["username"],
        "group_id": group_id,
        "audio_url": f"/voice/{audio_file_id}",
        "timestamp": datetime.utcnow().isoformat()
    }
    payload_ws = {"type": "new_group_voice_message", "data": message_data}
    await push_group_message(group["members"], current_user["username"], payload_ws)
    return JSONResponse({"message": "Голосовое сообщение отправлено в группу"}, status_code=201)

@router.get("/", response_model=List[MessageOut])
async def get_messages(current_user: dict = Depends(get_current_user)):
    raw_msgs = await get_messages_for_user(current_user["username"])
    result = []

    for msg in raw_msgs:
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

        result.append(MessageOut(
            sender=msg["sender"],
            receiver=msg["receiver"],
            content=decrypt_message(msg["content"]) if msg.get("content") else None,
            audio_url=audio_url,
            file_id=str(file_id) if file_id else None,
            file_url=file_url,
            filename=filename,
            timestamp=msg["timestamp"]
        ))

    return result

@router.post("/file")
async def send_file_message(
    receiver: str = Form(None),
    group_id: str = Form(None),
    file: UploadFile = File(None),
    file_id: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if not receiver and not group_id:
        raise HTTPException(400, detail="Нужно указать либо receiver, либо group_id")
    if receiver and group_id:
        raise HTTPException(400, detail="Нельзя указать одновременно receiver и group_id")

    if not file and not file_id:
        raise HTTPException(400, detail="Нужно передать либо file, либо file_id")
    if file and file_id:
        raise HTTPException(400, detail="Укажите либо file, либо file_id, не оба")

    # Загружаем файл, если передан
    uploaded_file_id = None
    if file:
        contents = await file.read()
        result_id = await fs_bucket.upload_from_stream(
            file.filename,
            contents,
            metadata={
                "user_id": current_user["username"],
                "content_type": file.content_type,
                "type": "generic"
            }
        )
        uploaded_file_id = str(result_id)
    else:
        # Проверка, существует ли указанный file_id
        try:
            file_obj = await fs_bucket.find({"_id": ObjectId(file_id)}).to_list(1)
            if not file_obj:
                raise HTTPException(404, detail="Указанный файл не найден")
            uploaded_file_id = file_id
        except Exception:
            raise HTTPException(400, detail="Неверный file_id")

    # Сохраняем сообщение
    if receiver:
        rec_user = await get_user(receiver)
        if not rec_user:
            raise HTTPException(404, detail="Получатель не найден")

        await create_message(
            sender=current_user["username"],
            receiver=receiver,
            content=None,
            audio_file_id=None,
            file_id=uploaded_file_id  # ← Новый аргумент в функции
        )
        return {"message": "Файл отправлен в личку"}

    group = await get_group_by_id(group_id)
    if not group:
        raise HTTPException(404, detail="Группа не найдена")
    if current_user["username"] not in group["members"]:
        raise HTTPException(403, detail="Вы не состоите в группе")

    await db.group_messages.insert_one({
        "group_id": group_id,
        "sender": current_user["username"],
        "content": None,
        "audio_file_id": None,
        "file_id": uploaded_file_id,
        "timestamp": datetime.utcnow()
    })
    return {"message": "Файл отправлен в группу"}