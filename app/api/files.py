from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from bson import ObjectId

from app.schemas import FileMeta
from app.api.auth import get_current_user
from app.db.mongodb import fs_bucket, db, count_user_files
from app.options import MAX_FILE_SIZE, MAX_FILE_COUNT

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/", response_model=dict)
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(400, "Too big")
    user = current_user["username"]
    if await count_user_files(user) >= MAX_FILE_COUNT:
        raise HTTPException(400, "Too many files")
    fid = await fs_bucket.upload_from_stream(
        file.filename, data, metadata={"user_id": user, "content_type": file.content_type}
    )
    return {"file_id": str(fid)}

@router.get("/", response_model=List[FileMeta])
async def list_files(current_user: dict = Depends(get_current_user)):
    user = current_user["username"]
    cursor = db.fs.files.find({"metadata.user_id": user})
    out = []
    async for d in cursor:
        out.append(FileMeta(
            filename=d["filename"],
            content_type=d["metadata"]["content_type"],
            uploaded_at=int(d["uploadDate"].timestamp())
        ))
    return out

@router.delete("/{file_id}", response_model=dict)
async def delete_file(file_id: str, current_user: dict = Depends(get_current_user)):
    try:
        await fs_bucket.delete(ObjectId(file_id))
    except:
        raise HTTPException(404, "Not found")
    return {"message": "Deleted"}