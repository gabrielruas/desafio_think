def get_openapi_schema(base_url):
    return {
        'openapi': '3.0.3',
        'info': {
            'title': 'Think Produto API',
            'version': '1.0.0',
            'description': 'API de autenticacao com usuarios no PostgreSQL e produtos no MongoDB.',
        },
        'servers': [
            {'url': base_url},
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
                        'username': {'type': 'string', 'example': 'usuario_teste'},
                        'email': {'type': 'string', 'format': 'email', 'example': 'usuario@example.com'},
                        'password': {
                            'type': 'string',
                            'format': 'password',
                            'writeOnly': True,
                            'example': 'senha_segura',
                        },
                    },
                },
                'LoginRequest': {
                    'type': 'object',
                    'required': ['password'],
                    'properties': {
                        'username': {'type': 'string', 'example': 'usuario_teste'},
                        'email': {'type': 'string', 'format': 'email', 'example': 'usuario@example.com'},
                        'password': {
                            'type': 'string',
                            'format': 'password',
                            'writeOnly': True,
                            'example': 'senha_segura',
                        },
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
                    'requestBody': _json_body_ref('RegisterRequest'),
                    'responses': {
                        '201': _json_response('Usuario criado', 'UserResponse'),
                        '400': {'description': 'Payload invalido'},
                        '409': {'description': 'Usuario ou email ja cadastrado'},
                    },
                }
            },
            '/auth/login': {
                'post': {
                    'tags': ['Autenticacao'],
                    'summary': 'Login',
                    'requestBody': _json_body_ref('LoginRequest'),
                    'responses': {
                        '200': _json_response('Token JWT gerado', 'TokenResponse'),
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
                        '200': _json_response('Usuario autenticado', 'UserResponse'),
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
                        '200': _json_response('Lista de produtos', 'ProductListResponse'),
                    },
                },
                'post': {
                    'tags': ['Produtos'],
                    'summary': 'Criar produto',
                    'security': [{'bearerAuth': []}],
                    'requestBody': _json_body_ref('ProductRequest'),
                    'responses': {
                        '201': _json_response('Produto criado', 'ProductResponse'),
                        '400': {'description': 'Dados invalidos'},
                        '401': {'description': 'Token invalido ou ausente'},
                    },
                },
            },
            '/products/{product_id}': {
                'get': {
                    'tags': ['Produtos'],
                    'summary': 'Buscar produto por ID',
                    'parameters': [_product_id_parameter()],
                    'responses': {
                        '200': _json_response('Produto encontrado', 'ProductResponse'),
                        '404': {'description': 'Produto nao encontrado'},
                    },
                },
                'put': {
                    'tags': ['Produtos'],
                    'summary': 'Atualizar produto completo',
                    'security': [{'bearerAuth': []}],
                    'parameters': [_product_id_parameter()],
                    'requestBody': _json_body_ref('ProductRequest'),
                    'responses': {
                        '200': _json_response('Produto atualizado', 'ProductResponse'),
                        '400': {'description': 'Dados invalidos'},
                        '401': {'description': 'Token invalido ou ausente'},
                        '404': {'description': 'Produto nao encontrado'},
                    },
                },
                'patch': {
                    'tags': ['Produtos'],
                    'summary': 'Atualizar produto parcial',
                    'security': [{'bearerAuth': []}],
                    'parameters': [_product_id_parameter()],
                    'requestBody': _json_body_ref('ProductUpdateRequest'),
                    'responses': {
                        '200': _json_response('Produto atualizado', 'ProductResponse'),
                        '400': {'description': 'Dados invalidos'},
                        '401': {'description': 'Token invalido ou ausente'},
                        '404': {'description': 'Produto nao encontrado'},
                    },
                },
                'delete': {
                    'tags': ['Produtos'],
                    'summary': 'Excluir produto',
                    'security': [{'bearerAuth': []}],
                    'parameters': [_product_id_parameter()],
                    'responses': {
                        '204': {'description': 'Produto excluido'},
                        '401': {'description': 'Token invalido ou ausente'},
                        '404': {'description': 'Produto nao encontrado'},
                    },
                },
            },
        },
    }


def get_swagger_html():
    return """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <title>Think Produto API - Swagger</title>
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
    """.strip()


def _json_body_ref(schema_name):
    return {
        'required': True,
        'content': {
            'application/json': {
                'schema': {'$ref': f'#/components/schemas/{schema_name}'}
            }
        },
    }


def _json_response(description, schema_name):
    return {
        'description': description,
        'content': {
            'application/json': {
                'schema': {'$ref': f'#/components/schemas/{schema_name}'}
            }
        },
    }


def _product_id_parameter():
    return {
        'name': 'product_id',
        'in': 'path',
        'required': True,
        'schema': {'type': 'string'},
    }
