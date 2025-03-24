# storage.py

from pymongo import MongoClient
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["neuronudgebot"]
users = db["users"]

# Sync Mongo functions
def _get_user_sync(user_id):
    return users.find_one({"user_id": user_id})

def _save_user_sync(user_id, data):
    users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

def _update_user_field_sync(user_id, field, value):
    users.update_one(
        {"user_id": user_id},
        {"$set": {field: value}}
    )

# Async wrappers
async def get_user(user_id):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_user_sync, user_id)

async def save_user(user_id, data):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_user_sync, user_id, data)

async def update_user_field(user_id, field, value):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _update_user_field_sync, user_id, field, value)
