from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
from app.db.mongodb import voice_fs_bucket

router = APIRouter(prefix="/voice", tags=["voice"])

@router.get("/{file_id}")
async def get_voice(file_id: str):
    try:
        stream = await voice_fs_bucket.open_download_stream(ObjectId(file_id))
        return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))
    except Exception:
        raise HTTPException(status_code=404, detail="File not found") 