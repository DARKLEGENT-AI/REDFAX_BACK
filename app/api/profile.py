from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from bson import ObjectId
from datetime import datetime

from app.schemas import UserProfile, UserProfileUpdate
from app.api.auth import get_current_user
from app.db.mongodb import get_user_profile, update_user_profile, fs_bucket, db
from app.db.mongodb import convert_date_fields

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    prof = await get_user_profile(current_user["username"])
    if not prof:
        raise HTTPException(404, "Not found")
    return convert_date_fields(prof)

@router.put("/", response_model=dict)
async def update_profile(data: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    upd = {k: v for k,v in data.dict().items() if v is not None}
    await update_user_profile(current_user["username"], upd)
    return {"message": "Updated"}

@router.post("/avatar", response_model=dict)
async def upload_avatar(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Must be image")
    user = current_user["username"]
    doc = await db.users.find_one({"username": user})
    old = doc.get("avatar_id")
    if old:
        try: await fs_bucket.delete(ObjectId(old))
        except: pass
    data = await file.read()
    new_id = await fs_bucket.upload_from_stream(
        file.filename, data,
        metadata={"user_id": user, "content_type": file.content_type, "uploaded_at": datetime.utcnow().isoformat()}
    )
    await db.users.update_one({"username": user}, {"$set": {"avatar_id": str(new_id)}})
    return {"message": "Avatar uploaded", "avatar_url": "/profile/avatar"}

@router.get("/avatar")
async def get_avatar(current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    doc = await db.users.find_one({"username": user})
    aid = doc.get("avatar_id")
    if not aid:
        raise HTTPException(404, "No avatar")
    stream = await fs_bucket.open_download_stream(ObjectId(aid))
    return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))