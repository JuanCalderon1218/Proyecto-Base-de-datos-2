from pymongo import AsyncMongoClient

from backend.app.config.settings import settings


client = AsyncMongoClient(settings.mongo_uri)

database = client[settings.mongo_db]