import base64
import hashlib
import hmac
import json
import time

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def _base64url_encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _base64url_decode(value):
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _create_access_token(user):
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

    header_value = _base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_value = _base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    unsigned_token = f'{header_value}.{payload_value}'
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode('utf-8'),
        unsigned_token.encode('ascii'),
        hashlib.sha256,
    ).digest()

    return f'{unsigned_token}.{_base64url_encode(signature)}'


def _decode_access_token(token):
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
        received_signature = _base64url_decode(signature_value)
        payload = json.loads(_base64url_decode(payload_value))
    except (ValueError, json.JSONDecodeError):
        return None

    if not hmac.compare_digest(expected_signature, received_signature):
        return None

    if payload.get('type') != 'access':
        return None

    if int(payload.get('exp', 0)) < int(time.time()):
        return None

    return payload


def _current_user_from_request(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None

    payload = _decode_access_token(auth_header.removeprefix('Bearer ').strip())
    if not payload:
        return None

    User = get_user_model()
    try:
        return User.objects.get(id=payload.get('sub'), is_active=True)
    except User.DoesNotExist:
        return None


@csrf_exempt
@require_POST
def register(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not username or not email or not password:
        return JsonResponse(
            {'detail': 'Informe username, email e password.'},
            status=400,
        )

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        return JsonResponse({'detail': 'Username ja cadastrado.'}, status=409)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'detail': 'Email ja cadastrado.'}, status=409)

    user = User.objects.create_user(username=username, email=email, password=password)

    return JsonResponse(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        },
        status=201,
    )


@csrf_exempt
@require_POST
def login(request):
    data = _json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    login_value = (data.get('username') or data.get('email') or '').strip()
    password = data.get('password') or ''

    if not login_value or not password:
        return JsonResponse({'detail': 'Informe username/email e password.'}, status=400)

    username = login_value
    if '@' in login_value:
        User = get_user_model()
        try:
            username = User.objects.get(email=login_value).get_username()
        except User.DoesNotExist:
            username = login_value

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': 'Credenciais invalidas.'}, status=401)

    return JsonResponse(
        {
            'access_token': _create_access_token(user),
            'token_type': 'bearer',
        }
    )


@require_GET
def me(request):
    user = _current_user_from_request(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    return JsonResponse(
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
        }
    )
