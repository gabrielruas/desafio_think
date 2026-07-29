import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .auth import AuthService
from .repositories import ProductRepository
from .schemas import (
    serialize_user,
    validate_login_payload,
    validate_product_payload,
    validate_register_payload,
)
from .services import ProductService
from .swagger import get_openapi_schema, get_swagger_html


def json_body(request):
    # Mantem o parse JSON em um unico ponto para padronizar erro nos controladores.
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def auth_service():
    # Fabrica simples para instanciar o servico usado pelos controladores.
    return AuthService()


def product_service():
    # Fabrica simples para manter views desacopladas da construcao do servico.
    return ProductService()


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
      <p style="margin-top: 24px;">Credenciais administrativas devem ser fornecidas pelo responsavel do ambiente.</p>
    </main>
  </body>
</html>
        """.strip(),
        content_type='text/html',
    )


@csrf_exempt
@require_POST
def register(request):
    payload, validation_error = validate_register_payload(json_body(request))
    if validation_error:
        return JsonResponse(validation_error, status=400)

    data, service_error, status_code = auth_service().register(payload)
    if service_error:
        return JsonResponse(service_error, status=status_code)

    return JsonResponse(data, status=status_code)


@csrf_exempt
@require_POST
def login(request):
    payload, validation_error = validate_login_payload(json_body(request))
    if validation_error:
        return JsonResponse(validation_error, status=400)

    data, service_error, status_code = auth_service().login(request, payload)
    if service_error:
        return JsonResponse(service_error, status=status_code)

    return JsonResponse(data, status=status_code)


@require_GET
def me(request):
    user = auth_service().current_user(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    return JsonResponse(serialize_user(user))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def products(request):
    service = product_service()

    if request.method == 'GET':
        status_filter = (request.GET.get('status') or '').strip().lower()
        data, service_error, status_code = service.list_products(status=status_filter)
        if service_error:
            return JsonResponse(service_error, status=status_code)
        return JsonResponse(data, status=status_code)

    user = auth_service().current_user(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    product, validation_error = validate_product_payload(json_body(request))
    if validation_error:
        return JsonResponse(validation_error, status=400)

    data, service_error, status_code = service.create_product(product)
    if service_error:
        return JsonResponse(service_error, status=status_code)

    return JsonResponse(data, status=status_code)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def product_detail(request, product_id):
    if ProductRepository.parse_id(product_id) is None:
        return JsonResponse({'detail': 'ID de produto invalido.'}, status=400)

    service = product_service()

    if request.method == 'GET':
        data, service_error, status_code = service.get_product(product_id)
        if service_error:
            return JsonResponse(service_error, status=status_code)
        return JsonResponse(data, status=status_code)

    user = auth_service().current_user(request)
    if user is None:
        return JsonResponse({'detail': 'Token invalido ou ausente.'}, status=401)

    if request.method == 'DELETE':
        data, service_error, status_code = service.delete_product(product_id)
        if service_error:
            return JsonResponse(service_error, status=status_code)
        return HttpResponse(status=status_code)

    partial = request.method == 'PATCH'
    product, validation_error = validate_product_payload(json_body(request), partial=partial)
    if validation_error:
        return JsonResponse(validation_error, status=400)

    if not product:
        return JsonResponse({'detail': 'Informe ao menos um campo para atualizar.'}, status=400)

    data, service_error, status_code = service.update_product(product_id, product)
    if service_error:
        return JsonResponse(service_error, status=status_code)

    return JsonResponse(data, status=status_code)


@require_GET
def openapi_schema(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    return JsonResponse(get_openapi_schema(base_url))


@require_GET
def swagger_ui(request):
    return HttpResponse(get_swagger_html(), content_type='text/html')
