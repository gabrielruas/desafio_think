import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient


@require_GET
def home(request):
    return HttpResponse(
        """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Think Produto</title>
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        font-family: Arial, sans-serif;
        background: #f5f7fb;
        color: #172033;
        display: grid;
        place-items: center;
      }
      main {
        width: min(720px, calc(100% - 32px));
        background: #ffffff;
        border: 1px solid #d8deea;
        border-radius: 8px;
        padding: 32px;
        box-shadow: 0 12px 32px rgba(23, 32, 51, 0.08);
      }
      h1 {
        margin: 0 0 8px;
        font-size: 28px;
      }
      p {
        margin: 0 0 24px;
        color: #526071;
      }
      nav {
        display: grid;
        gap: 12px;
      }
      a {
        display: block;
        padding: 14px 16px;
        border: 1px solid #c8d0df;
        border-radius: 6px;
        color: #172033;
        text-decoration: none;
        font-weight: 700;
      }
      a:hover {
        background: #edf2f7;
      }
      code {
        color: #344256;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Think Produto</h1>
      <p>Painel inicial da aplicacao. Use o Django Admin para gerenciar usuarios.</p>
      <nav>
        <a href="/admin/">Django Admin</a>
        <a href="/swagger/">Swagger da API</a>
        <a href="/openapi.json">OpenAPI JSON</a>
      </nav>
      <p style="margin-top: 24px;">Login admin: <code>gabriel</code> / <code>123456</code></p>
    </main>
  </body>
</html>
        """.strip(),
        content_type='text/html',
    )


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def _products_collection():
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[settings.MONGO_DB]['products']


def _product_to_json(product):
    return {
        'id': str(product['_id']),
        'nome': product['nome'],
        'descricao': product['descricao'],
        'preco': float(product['preco']),
        'status': product['status'],
        'data_criacao': product['data_criacao'].isoformat(),
    }


def _parse_product_id(product_id):
    try:
        return ObjectId(product_id)
    except InvalidId:
        return None


def _validate_product_payload(data, partial=False):
    if data is None:
        return None, {'detail': 'JSON invalido.'}

    errors = {}
    product = {}

    if not partial or 'nome' in data:
        nome = (data.get('nome') or '').strip()
        if not nome:
            errors['nome'] = 'Informe o nome do produto.'
        else:
            product['nome'] = nome

    if not partial or 'descricao' in data:
        descricao = (data.get('descricao') or '').strip()
        if not descricao:
            errors['descricao'] = 'Informe a descricao do produto.'
        else:
            product['descricao'] = descricao

    if not partial or 'preco' in data:
        try:
            preco = Decimal(str(data.get('preco')))
        except (InvalidOperation, TypeError):
            errors['preco'] = 'Informe um preco valido.'
        else:
            if preco < 0:
                errors['preco'] = 'O preco nao pode ser negativo.'
            else:
                product['preco'] = float(preco)

    if not partial or 'status' in data:
        status = (data.get('status') or '').strip().lower()
        if status not in {'ativo', 'inativo'}:
            errors['status'] = 'Status deve ser ativo ou inativo.'
        else:
            product['status'] = status

    if errors:
        return None, {'detail': 'Dados invalidos.', 'errors': errors}

    return product, None


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


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def products(request):
    collection = _products_collection()

    if request.method == 'GET':
        status = (request.GET.get('status') or '').strip().lower()
        query = {}
        if status:
            if status not in {'ativo', 'inativo'}:
                return JsonResponse({'detail': 'Status deve ser ativo ou inativo.'}, status=400)
            query['status'] = status

        items = [_product_to_json(product) for product in collection.find(query).sort('data_criacao', -1)]
        return JsonResponse({'results': items})

    user = _current_user_from_request(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    product, error = _validate_product_payload(_json_body(request))
    if error:
        return JsonResponse(error, status=400)

    product['data_criacao'] = datetime.now(timezone.utc)
    result = collection.insert_one(product)
    created = collection.find_one({'_id': result.inserted_id})

    return JsonResponse(_product_to_json(created), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def product_detail(request, product_id):
    object_id = _parse_product_id(product_id)
    if object_id is None:
        return JsonResponse({'detail': 'ID de produto invalido.'}, status=400)

    collection = _products_collection()

    if request.method == 'GET':
        product = collection.find_one({'_id': object_id})
        if product is None:
            return JsonResponse({'detail': 'Produto nao encontrado.'}, status=404)
        return JsonResponse(_product_to_json(product))

    user = _current_user_from_request(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    if request.method == 'DELETE':
        result = collection.delete_one({'_id': object_id})
        if result.deleted_count == 0:
            return JsonResponse({'detail': 'Produto nao encontrado.'}, status=404)
        return HttpResponse(status=204)

    partial = request.method == 'PATCH'
    product, error = _validate_product_payload(_json_body(request), partial=partial)
    if error:
        return JsonResponse(error, status=400)

    if not product:
        return JsonResponse({'detail': 'Informe ao menos um campo para atualizar.'}, status=400)

    result = collection.update_one({'_id': object_id}, {'$set': product})
    if result.matched_count == 0:
        return JsonResponse({'detail': 'Produto nao encontrado.'}, status=404)

    updated = collection.find_one({'_id': object_id})
    return JsonResponse(_product_to_json(updated))


@require_GET
def openapi_schema(request):
    return JsonResponse(
        {
            'openapi': '3.0.3',
            'info': {
                'title': 'Think Produto Auth API',
                'version': '1.0.0',
                'description': 'API de autenticacao com usuarios no PostgreSQL.',
            },
            'servers': [
                {'url': request.build_absolute_uri('/').rstrip('/')},
            ],
            'components': {
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT',
                    }
                },
                'schemas': {
                    'RegisterRequest': {
                        'type': 'object',
                        'required': ['username', 'email', 'password'],
                        'properties': {
                            'username': {'type': 'string', 'example': 'gabriel'},
                            'email': {'type': 'string', 'format': 'email', 'example': 'gabriel@email.com'},
                            'password': {'type': 'string', 'format': 'password', 'example': '123456'},
                        },
                    },
                    'LoginRequest': {
                        'type': 'object',
                        'required': ['password'],
                        'properties': {
                            'username': {'type': 'string', 'example': 'gabriel'},
                            'email': {'type': 'string', 'format': 'email', 'example': 'gabriel@email.com'},
                            'password': {'type': 'string', 'format': 'password', 'example': '123456'},
                        },
                    },
                    'TokenResponse': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'},
                            'token_type': {'type': 'string', 'example': 'bearer'},
                        },
                    },
                    'UserResponse': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'is_active': {'type': 'boolean'},
                        },
                    },
                    'ErrorResponse': {
                        'type': 'object',
                        'properties': {
                            'detail': {'type': 'string'},
                        },
                    },
                    'ProductRequest': {
                        'type': 'object',
                        'required': ['nome', 'descricao', 'preco', 'status'],
                        'properties': {
                            'nome': {'type': 'string', 'example': 'Notebook'},
                            'descricao': {'type': 'string', 'example': 'Notebook para desenvolvimento'},
                            'preco': {'type': 'number', 'format': 'float', 'example': 4500.90},
                            'status': {'type': 'string', 'enum': ['ativo', 'inativo'], 'example': 'ativo'},
                        },
                    },
                    'ProductUpdateRequest': {
                        'type': 'object',
                        'properties': {
                            'nome': {'type': 'string', 'example': 'Notebook'},
                            'descricao': {'type': 'string', 'example': 'Notebook atualizado'},
                            'preco': {'type': 'number', 'format': 'float', 'example': 4299.90},
                            'status': {'type': 'string', 'enum': ['ativo', 'inativo'], 'example': 'inativo'},
                        },
                    },
                    'ProductResponse': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'example': '66a6d9678c8f3d48e9f44b11'},
                            'nome': {'type': 'string'},
                            'descricao': {'type': 'string'},
                            'preco': {'type': 'number', 'format': 'float'},
                            'status': {'type': 'string', 'enum': ['ativo', 'inativo']},
                            'data_criacao': {'type': 'string', 'format': 'date-time'},
                        },
                    },
                    'ProductListResponse': {
                        'type': 'object',
                        'properties': {
                            'results': {
                                'type': 'array',
                                'items': {'$ref': '#/components/schemas/ProductResponse'},
                            }
                        },
                    },
                },
            },
            'paths': {
                '/auth/register': {
                    'post': {
                        'tags': ['Autenticacao'],
                        'summary': 'Cadastrar usuario',
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/RegisterRequest'}
                                }
                            },
                        },
                        'responses': {
                            '201': {
                                'description': 'Usuario criado',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/UserResponse'}
                                    }
                                },
                            },
                            '400': {'description': 'Payload invalido'},
                            '409': {'description': 'Usuario ou email ja cadastrado'},
                        },
                    }
                },
                '/auth/login': {
                    'post': {
                        'tags': ['Autenticacao'],
                        'summary': 'Login',
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/LoginRequest'}
                                }
                            },
                        },
                        'responses': {
                            '200': {
                                'description': 'Token JWT gerado',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/TokenResponse'}
                                    }
                                },
                            },
                            '400': {'description': 'Payload invalido'},
                            '401': {'description': 'Credenciais invalidas'},
                        },
                    }
                },
                '/auth/me': {
                    'get': {
                        'tags': ['Autenticacao'],
                        'summary': 'Buscar usuario autenticado',
                        'security': [{'bearerAuth': []}],
                        'responses': {
                            '200': {
                                'description': 'Usuario autenticado',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/UserResponse'}
                                    }
                                },
                            },
                            '401': {'description': 'Token invalido ou ausente'},
                        },
                    }
                },
                '/products': {
                    'get': {
                        'tags': ['Produtos'],
                        'summary': 'Listar produtos',
                        'parameters': [
                            {
                                'name': 'status',
                                'in': 'query',
                                'required': False,
                                'schema': {'type': 'string', 'enum': ['ativo', 'inativo']},
                            }
                        ],
                        'responses': {
                            '200': {
                                'description': 'Lista de produtos',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/ProductListResponse'}
                                    }
                                },
                            }
                        },
                    },
                    'post': {
                        'tags': ['Produtos'],
                        'summary': 'Criar produto',
                        'security': [{'bearerAuth': []}],
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/ProductRequest'}
                                }
                            },
                        },
                        'responses': {
                            '201': {
                                'description': 'Produto criado',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/ProductResponse'}
                                    }
                                },
                            },
                            '400': {'description': 'Dados invalidos'},
                            '401': {'description': 'Token invalido ou ausente'},
                        },
                    },
                },
                '/products/{product_id}': {
                    'get': {
                        'tags': ['Produtos'],
                        'summary': 'Buscar produto por ID',
                        'parameters': [
                            {
                                'name': 'product_id',
                                'in': 'path',
                                'required': True,
                                'schema': {'type': 'string'},
                            }
                        ],
                        'responses': {
                            '200': {
                                'description': 'Produto encontrado',
                                'content': {
                                    'application/json': {
                                        'schema': {'$ref': '#/components/schemas/ProductResponse'}
                                    }
                                },
                            },
                            '404': {'description': 'Produto nao encontrado'},
                        },
                    },
                    'put': {
                        'tags': ['Produtos'],
                        'summary': 'Atualizar produto completo',
                        'security': [{'bearerAuth': []}],
                        'parameters': [
                            {
                                'name': 'product_id',
                                'in': 'path',
                                'required': True,
                                'schema': {'type': 'string'},
                            }
                        ],
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/ProductRequest'}
                                }
                            },
                        },
                        'responses': {
                            '200': {'description': 'Produto atualizado'},
                            '400': {'description': 'Dados invalidos'},
                            '401': {'description': 'Token invalido ou ausente'},
                            '404': {'description': 'Produto nao encontrado'},
                        },
                    },
                    'patch': {
                        'tags': ['Produtos'],
                        'summary': 'Atualizar produto parcial',
                        'security': [{'bearerAuth': []}],
                        'parameters': [
                            {
                                'name': 'product_id',
                                'in': 'path',
                                'required': True,
                                'schema': {'type': 'string'},
                            }
                        ],
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/ProductUpdateRequest'}
                                }
                            },
                        },
                        'responses': {
                            '200': {'description': 'Produto atualizado'},
                            '400': {'description': 'Dados invalidos'},
                            '401': {'description': 'Token invalido ou ausente'},
                            '404': {'description': 'Produto nao encontrado'},
                        },
                    },
                    'delete': {
                        'tags': ['Produtos'],
                        'summary': 'Excluir produto',
                        'security': [{'bearerAuth': []}],
                        'parameters': [
                            {
                                'name': 'product_id',
                                'in': 'path',
                                'required': True,
                                'schema': {'type': 'string'},
                            }
                        ],
                        'responses': {
                            '204': {'description': 'Produto excluido'},
                            '401': {'description': 'Token invalido ou ausente'},
                            '404': {'description': 'Produto nao encontrado'},
                        },
                    },
                },
            },
        }
    )


@require_GET
def swagger_ui(request):
    return HttpResponse(
        """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <title>Think Produto Auth API - Swagger</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function () {
        window.ui = SwaggerUIBundle({
          url: "/openapi.json",
          dom_id: "#swagger-ui",
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout"
        });
      };
    </script>
  </body>
</html>
        """.strip(),
        content_type='text/html',
    )
