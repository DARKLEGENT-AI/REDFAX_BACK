from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

from app.options import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

fs_bucket = AsyncIOMotorGridFSBucket(db)
voice_fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="voice_fs")
avatar_fs_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="avatars")