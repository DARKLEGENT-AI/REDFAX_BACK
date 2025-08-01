from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from bson import ObjectId, errors as bson_errors
from app.db.mongodb import *
from app.options import MAX_FILE_SIZE, MAX_FILE_COUNT
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/files", tags=["files"])

### ФАЙЛЫ ###

@router.post("/")
async def upload_file(user_id: str, file: UploadFile = File(...)):
    contents = await file.read()

    # ⛔ Проверка размера файла
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="Файл превышает максимальный размер 50 МБ")

    # ⛔ Проверка количества файлов
    file_count = await count_user_files(user_id)
    if file_count >= MAX_FILE_COUNT:
        raise HTTPException(400, detail="Превышено максимальное количество файлов: 20")

    # ✅ Загрузка
    file_id = await fs_bucket.upload_from_stream(
        file.filename,
        contents,
        metadata={"user_id": user_id, "content_type": file.content_type}
    )

    return {"file_id": str(file_id)}

@router.get("/")
async def list_files(user_id: str):
    cursor = db.fs.files.find({"metadata.user_id": user_id})
    files = []
    async for doc in cursor:
        files.append({
            "file_id": str(doc["_id"]),
            "filename": doc["filename"],
            "content_type": doc["metadata"].get("content_type"),
        })
    return files

@router.get("/{file_id}")
async def get_file(file_id: str):
    try:
        stream = await fs_bucket.open_download_stream(ObjectId(file_id))
        return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    
@router.get("/voice/{file_id}")
async def get_file(file_id: str):
    try:
        stream = await voice_fs_bucket.open_download_stream(ObjectId(file_id))
        return StreamingResponse(stream, media_type=stream.metadata.get("content_type"))
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    
@router.delete("/{file_id}")
async def delete_file(file_id: str):
    try:
        oid = ObjectId(file_id)
        await fs_bucket.delete(oid)
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@router.post("/text")
async def upload_text_file(
    user_id: str,
    file: UploadFile = File(...),
):
    # Проверяем, что файл текстовый (опционально)
    if not file.content_type.startswith("text/"):
        raise HTTPException(status_code=400, detail="Можно загружать только текстовые файлы")

    contents = await file.read()  # bytes
    # Можно проверить размер, если нужно

    # Загружаем в GridFS
    file_id = await fs_bucket.upload_from_stream(
        file.filename,
        contents,
        metadata={"user_id": user_id, "content_type": file.content_type}
    )

    return {"file_id": str(file_id)}

@router.put("/text/{file_id}")
async def update_text_file_in_gridfs(
    file_id: str,
    file: UploadFile = File(...),
    user_id: str = Query(...),
):
    # Проверяем, что файл текстовый
    if not file.content_type.startswith("text/"):
        raise HTTPException(status_code=400, detail="Можно загружать только текстовые файлы")

    # Удаляем старый файл из GridFS
    await fs_bucket.delete(ObjectId(file_id))

    contents = await file.read()
    # Загружаем новый файл
    new_file_id = await fs_bucket.upload_from_stream(
        file.filename,
        contents,
        metadata={"user_id": user_id, "content_type": file.content_type}
    )

    return {"new_file_id": str(new_file_id)}