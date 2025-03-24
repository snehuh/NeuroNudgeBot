from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["nudgebot"]
users = db["users"]

def get_user(user_id):
    return users.find_one({"user_id": user_id})

def save_user(user_id, data):
    users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

def update_user_field(user_id, field, value):
    users.update_one(
        {"user_id": user_id},
        {"$set": {field: value}}
    )
