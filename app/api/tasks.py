from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas import TaskCreate, TaskOut
from app.api.auth import get_current_user
from app.db.mongodb import create_task, get_tasks_by_user, delete_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

### ЗАДАЧИ ###

@router.post("/", response_model=dict)
async def add_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    task_id = await create_task(current_user["username"], task)
    return {"message": "Task added", "id": task_id}

@router.get("/", response_model=List[TaskOut])
async def get_tasks(current_user: dict = Depends(get_current_user)):
    tasks = await get_tasks_by_user(current_user["username"])
    return tasks

@router.delete("/{task_id}", response_model=dict)
async def remove_task(task_id: str, current_user: dict = Depends(get_current_user)):
    deleted = await delete_task(task_id, current_user["username"])
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Task not found or not yours")
    return {"message": "Task deleted successfully"}
