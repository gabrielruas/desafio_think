from django.conf import settings
from pymongo import MongoClient


_mongo_client = None


def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client


def get_mongo_database():
    return get_mongo_client()[settings.MONGO_DB]


def get_products_collection():
    return get_mongo_database()['products']
