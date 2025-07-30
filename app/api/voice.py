from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId

from app.api.auth import get_current_user
from app.db.mongodb import voice_fs_bucket

router = APIRouter(prefix="/voice", tags=["voice"])

@router.get("/{file_id}")
async def get_voice(file_id: str, current_user: dict = Depends(get_current_user)):
    try:
        stream = await voice_fs_bucket.open_download_stream(ObjectId(file_id))
    except:
        raise HTTPException(404, "Not found")
    return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))