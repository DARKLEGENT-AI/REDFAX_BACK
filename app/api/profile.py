from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime
from app.schemas import UserProfile, UserProfileUpdate
from app.api.auth import get_current_user
from app.db.mongodb import update_user_profile, db, avatar_fs_bucket
from app.db.mongodb import convert_date_fields

router = APIRouter(prefix="/profile", tags=["profile"])

### ПРОФИЛЬ ###

@router.get("/", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"username": current_user["username"]})
    if not user:
        raise HTTPException(404, "Профиль не найден")

    return convert_date_fields({
        "avatar_url": user.get("avatar_url"),
        "birth_date": user.get("birth_date"),
        "bio": user.get("bio"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "gender": user.get("gender"),
        "city": user.get("city"),
        "country": user.get("country"),
    })

@router.put("/", response_model=dict)
async def update_profile(
    data: UserProfileUpdate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    await update_user_profile(current_user["username"], update_data)
    return {"message": "Profile updated"}

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Файл должен быть изображением")

    # --- 1) удаляем старый ---
    user_doc = await db.users.find_one({"username": current_user["username"]})
    old_id = user_doc.get("avatar_id")
    if old_id:
        try:
            await avatar_fs_bucket.delete(ObjectId(old_id))
        except:
            pass

    # --- 2) загружаем новый ---
    data = await file.read()
    new_id = await avatar_fs_bucket.upload_from_stream(
        file.filename, data,
        metadata={
            "user_id": current_user["username"],
            "content_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat()
        }
    )

    # --- 3) сохраняем avatar_id в профиле ---
    await db.users.update_one(
        {"username": current_user["username"]},
        {"$set": {"avatar_id": str(new_id)}}
    )

    return {"message": "Аватар загружен", "avatar_url": "/profile/avatar"}

@router.get("/avatar")
async def get_avatar(current_user: dict = Depends(get_current_user)):
    user_doc = await db.users.find_one({"username": current_user["username"]})
    avatar_id = user_doc.get("avatar_id")
    if not avatar_id:
        raise HTTPException(404, "Аватар не найден")

    try:
        stream = await avatar_fs_bucket.open_download_stream(ObjectId(avatar_id))
    except:
        raise HTTPException(404, "Аватар не найден")

    return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))
