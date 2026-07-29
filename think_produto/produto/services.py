from datetime import datetime, timezone

from .repositories import ProductRepository
from .schemas import VALID_PRODUCT_STATUS, serialize_product


class ProductService:
    def __init__(self, product_repository=None):
        self.product_repository = product_repository or ProductRepository()

    def list_products(self, status=None):
        if status and status not in VALID_PRODUCT_STATUS:
            return None, {'detail': 'Status deve ser ativo ou inativo.'}, 400

        products = self.product_repository.list(status=status)
        return {'results': [serialize_product(product) for product in products]}, None, 200

    def create_product(self, product):
        product['data_criacao'] = datetime.now(timezone.utc)
        created = self.product_repository.create(product)
        return serialize_product(created), None, 201

    def get_product(self, product_id):
        product = self.product_repository.get(product_id)
        if product is None:
            return None, {'detail': 'Produto nao encontrado.'}, 404
        return serialize_product(product), None, 200

    def update_product(self, product_id, product):
        updated = self.product_repository.update(product_id, product)
        if updated is None:
            return None, {'detail': 'Produto nao encontrado.'}, 404
        return serialize_product(updated), None, 200

    def delete_product(self, product_id):
        deleted = self.product_repository.delete(product_id)
        if not deleted:
            return None, {'detail': 'Produto nao encontrado.'}, 404
        return None, None, 204
