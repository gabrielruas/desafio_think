import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import authenticate

from .repositories import UserRepository
from .schemas import serialize_user


class JWTService:
    def create_access_token(self, user):
        now = int(time.time())
        payload = {
            'sub': str(user.id),
            'username': user.get_username(),
            'email': user.email,
            'type': 'access',
            'iat': now,
            'exp': now + settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS,
        }
        header = {'alg': 'HS256', 'typ': 'JWT'}

        header_value = self._base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_value = self._base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        unsigned_token = f'{header_value}.{payload_value}'
        signature = hmac.new(
            settings.JWT_SECRET_KEY.encode('utf-8'),
            unsigned_token.encode('ascii'),
            hashlib.sha256,
        ).digest()

        return f'{unsigned_token}.{self._base64url_encode(signature)}'

    def decode_access_token(self, token):
        try:
            header_value, payload_value, signature_value = token.split('.')
        except ValueError:
            return None

        unsigned_token = f'{header_value}.{payload_value}'
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.encode('utf-8'),
            unsigned_token.encode('ascii'),
            hashlib.sha256,
        ).digest()

        try:
            received_signature = self._base64url_decode(signature_value)
            payload = json.loads(self._base64url_decode(payload_value))
        except (ValueError, json.JSONDecodeError):
            return None

        if not hmac.compare_digest(expected_signature, received_signature):
            return None

        if payload.get('type') != 'access':
            return None

        if int(payload.get('exp', 0)) < int(time.time()):
            return None

        return payload

    @staticmethod
    def _base64url_encode(value):
        return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')

    @staticmethod
    def _base64url_decode(value):
        padding = '=' * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)


class AuthService:
    def __init__(self, user_repository=None, jwt_service=None):
        self.user_repository = user_repository or UserRepository()
        self.jwt_service = jwt_service or JWTService()

    def register(self, payload):
        if self.user_repository.exists_by_username(payload['username']):
            return None, {'detail': 'Username ja cadastrado.'}, 409

        if self.user_repository.exists_by_email(payload['email']):
            return None, {'detail': 'Email ja cadastrado.'}, 409

        user = self.user_repository.create(
            username=payload['username'],
            email=payload['email'],
            password=payload['password'],
        )
        return serialize_user(user), None, 201

    def login(self, request, payload):
        username = payload['login']
        if '@' in payload['login']:
            user = self.user_repository.get_by_email(payload['login'])
            if user is not None:
                username = user.get_username()

        user = authenticate(request, username=username, password=payload['password'])
        if user is None:
            return None, {'detail': 'Credenciais invalidas.'}, 401

        return {
            'access_token': self.jwt_service.create_access_token(user),
            'token_type': 'bearer',
        }, None, 200

    def current_user(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.removeprefix('Bearer ').strip()
        payload = self.jwt_service.decode_access_token(token)
        if not payload:
            return None

        return self.user_repository.get_active_by_id(payload.get('sub'))
