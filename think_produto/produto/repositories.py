from bson import ObjectId
from bson.errors import InvalidId
from django.contrib.auth import get_user_model

from .database import get_products_collection


class UserRepository:
    def __init__(self):
        self.model = get_user_model()

    def create(self, username, email, password):
        return self.model.objects.create_user(username=username, email=email, password=password)

    def exists_by_username(self, username):
        return self.model.objects.filter(username=username).exists()

    def exists_by_email(self, email):
        return self.model.objects.filter(email=email).exists()

    def get_by_email(self, email):
        try:
            return self.model.objects.get(email=email)
        except self.model.DoesNotExist:
            return None

    def get_active_by_id(self, user_id):
        try:
            return self.model.objects.get(id=user_id, is_active=True)
        except self.model.DoesNotExist:
            return None


class ProductRepository:
    def __init__(self):
        self.collection = get_products_collection()

    def list(self, status=None):
        query = {}
        if status:
            query['status'] = status
        return list(self.collection.find(query).sort('data_criacao', -1))

    def create(self, product):
        result = self.collection.insert_one(product)
        return self.get_by_object_id(result.inserted_id)

    def get(self, product_id):
        object_id = self.parse_id(product_id)
        if object_id is None:
            return None
        return self.get_by_object_id(object_id)

    def update(self, product_id, product):
        object_id = self.parse_id(product_id)
        if object_id is None:
            return None

        result = self.collection.update_one({'_id': object_id}, {'$set': product})
        if result.matched_count == 0:
            return None

        return self.get_by_object_id(object_id)

    def delete(self, product_id):
        object_id = self.parse_id(product_id)
        if object_id is None:
            return False
        return self.collection.delete_one({'_id': object_id}).deleted_count == 1

    def get_by_object_id(self, object_id):
        return self.collection.find_one({'_id': object_id})

    @staticmethod
    def parse_id(product_id):
        try:
            return ObjectId(product_id)
        except InvalidId:
            return None
