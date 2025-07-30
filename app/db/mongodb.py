from datetime import datetime
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.schemas import *
from bson import ObjectId
import secrets
from fastapi import FastAPI, Depends, HTTPException, Query
from app.utils.crypto import *

MONGO_URI = "mongodb://root:example@localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
db = client["messenger"]
fs_bucket = AsyncIOMotorGridFSBucket(db)
voice_fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="voice_fs")
avatar_fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="avatars")

# users: коллекция пользователей
users_collection = db.users

# tasks: коллекция задач
tasks_collection = db.tasks

async def get_user(username: str):
    return await db.users.find_one({"username": username})

async def create_user(username: str, hashed_password: str):
    return await db.users.insert_one({"username": username, "hashed_password": hashed_password})

async def create_message(sender, receiver, content=None, audio_file_id=None, file_id=None):
    await db.messages.insert_one({
        "sender": sender,
        "receiver": receiver,
        "content": content,
        "audio_file_id": audio_file_id,
        "file_id": file_id,
        "timestamp": datetime.utcnow()
    })

async def get_messages_for_user(username: str):
    cursor = db.messages.find({
        "$or": [{"sender": username}, {"receiver": username}]
    }).sort("timestamp")
    return await cursor.to_list(length=1000)

async def add_friend_db(user: str, friend: str):
    await db.friends.update_one(
        {"user": user},
        {"$addToSet": {"friends": friend}},
        upsert=True
    )
    await db.friends.update_one(
        {"user": friend},
        {"$addToSet": {"friends": user}},
        upsert=True
    )

async def get_friends(username: str):
    doc = await db.friends.find_one({"user": username})
    return doc["friends"] if doc else []

async def delete_chat(user: str, friend: str):
    await db.messages.delete_many({
        "$or": [
            {"sender": user, "receiver": friend},
            {"sender": friend, "receiver": user}
        ]
    })

def convert_date_fields(profile_data: dict) -> dict:
    bd = profile_data.get("birth_date")
    if bd is not None:
        # если получили date или datetime — конвертим в ISO‑строку
        if isinstance(bd, (date, datetime)):
            profile_data["birth_date"] = bd.isoformat()
        else:
            # если уже строка (или что‑то ещё) — приводим к str на всякий случай
            profile_data["birth_date"] = str(bd)
    return profile_data

async def update_user_profile(username: str, update_data: dict):
    # Этот метод теперь принимает любой ключ, включая 'avatar_id'
    await db.users.update_one(
        {"username": username},
        {"$set": update_data}
    )

async def get_user_profile(username: str):
    user = await users_collection.find_one(
        {"username": username},
        {"_id": 0, "country": 1, "city": 1, "birth_date": 1, "gender": 1, "languages": 1, "bio": 1, "nickname": 1}
    )
    return user or {}

async def create_task(username: str, task_data: TaskCreate):
    doc = {
        "username": username,
        "title": task_data.title,
        "date": str(task_data.date)  # или task_data.date.isoformat()
    }
    result = await tasks_collection.insert_one(doc)
    return str(result.inserted_id)

async def get_tasks_by_user(username: str):
    cursor = tasks_collection.find({"username": username})
    tasks = []
    async for doc in cursor:
        tasks.append({
            "id": str(doc["_id"]),
            "title": doc["title"],
            "date": doc["date"]
        })
    return tasks

async def delete_task(task_id: str, username: str):
    result = await db.tasks.delete_one({
        "_id": ObjectId(task_id),
        "username": username  # защищает от удаления чужих задач
    })
    return result.deleted_count

async def create_group(name: str, admin_username: str):
    invite_key = secrets.token_hex(6)
    result = await db.groups.insert_one({
        "name": name,
        "admin": admin_username,
        "members": [admin_username],
        "invite_key": invite_key,
    })
    return str(result.inserted_id), invite_key

async def get_group_by_invite_key(invite_key: str):
    return await db.groups.find_one({"invite_key": invite_key})

async def get_group_by_id(group_id: str):
    return await db.groups.find_one({"_id": ObjectId(group_id)})

async def add_user_to_group(invite_key: str, username: str, requester: str):
    group = await get_group_by_invite_key(invite_key)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group["admin"] != requester:
        raise HTTPException(status_code=403, detail="Only admin can add members")

    if username in group["members"]:
        raise HTTPException(status_code=400, detail="User already in group")

    await db.groups.update_one(
        {"_id": group["_id"]},
        {"$push": {"members": username}}
    )
    return group

async def delete_group(group_id: str, requester: str):
    group = await get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group["admin"] != requester:
        raise HTTPException(status_code=403, detail="Only admin can delete the group")

    await db.groups.delete_one({"_id": group["_id"]})

async def get_groups_for_user(username: str):
    cursor = db.groups.find({"members": username})
    groups = []
    async for group in cursor:
        groups.append({
            "id": str(group["_id"]),
            "name": group["name"],
            "admin": group["admin"],
            "invite_key": group["invite_key"],
            "members": group["members"],
        })
    return groups

async def send_group_message(sender: str, group_id: str, content: str):
    encrypted = encrypt_message(content)
    await db.group_messages.insert_one({
        "group_id": group_id,
        "sender": sender,
        "content": encrypted,
        "timestamp": datetime.utcnow()
    })

async def get_group_by_id(group_id: str):
    return await db.groups.find_one({"_id": ObjectId(group_id)})

async def get_group_messages(group_id: str):
    cursor = db.group_messages.find({"group_id": group_id}).sort("timestamp", 1)
    messages = []
    async for msg in cursor:
        messages.append({
            "sender": msg["sender"],
            "content": decrypt_message(msg["content"]),
            "timestamp": msg["timestamp"],
        })
    return messages

async def count_user_files(user_id: str) -> int:
    return await db.fs.files.count_documents({"metadata.user_id": user_id})

