# database_util.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("key")
if not uri:
    raise ValueError("MongoDB connection string not found in environment variables")

client = MongoClient(uri, server_api=ServerApi('1'))
db = client["chat"]

def get_collection(collection_name):
    return db[collection_name]
