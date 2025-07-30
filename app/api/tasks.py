from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas import TaskCreate, TaskOut
from app.api.auth import get_current_user
from app.db.mongodb import create_task, get_tasks_by_user, delete_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=dict)
async def add_task(data: TaskCreate, current_user: dict = Depends(get_current_user)):
    tid = await create_task(current_user["username"], data)
    return {"message": "Added", "id": tid}

@router.get("/", response_model=List[TaskOut])
async def list_tasks(current_user: dict = Depends(get_current_user)):
    return await get_tasks_by_user(current_user["username"])

@router.delete("/{task_id}", response_model=dict)
async def del_task(task_id: str, current_user: dict = Depends(get_current_user)):
    if not await delete_task(task_id, current_user["username"]):
        raise HTTPException(404, "Not found or not yours")
    return {"message": "Deleted"}