# Think Produto

API Django para autenticacao de usuarios com PostgreSQL e CRUD de produtos com MongoDB.

## Visao Geral

O projeto separa os bancos por responsabilidade:

- PostgreSQL: usuarios, permissoes, grupos, sessoes e Django Admin.
- MongoDB: produtos.

A aplicacao expoe:

- Django Admin em `/admin/`.
- Swagger em `/swagger/`.
- OpenAPI em `/openapi.json`.
- Rotas de autenticacao em `/auth/*`.
- Rotas de produtos em `/products`.

## Tecnologias

- Python 3.13
- Django 6.0.7
- PostgreSQL 16
- MongoDB 7
- PyMongo
- Docker Compose
- JWT HS256 implementado na aplicacao

## Arquitetura E Design Patterns

O app `produto` foi organizado em camadas para evitar regras de negocio concentradas nas views.

```text
produto/
├── views.py          # Controladores HTTP
├── services.py       # Camada de servico: regras de negocio
├── repositories.py   # Padrao Repositorio: acesso a dados
├── schemas.py        # Validacao e serializacao
├── auth.py           # JWT e autenticacao
├── database.py       # Provedor/fabrica de conexao MongoDB
├── swagger.py        # OpenAPI e Swagger UI
├── urls.py           # Rotas da aplicacao
├── admin.py          # Registro de modelos no Django Admin
└── models.py         # Modelos Django, se necessarios
```

Fluxo de uma requisicao:

```text
Request HTTP
  -> views.py
  -> schemas.py
  -> services.py
  -> repositories.py
  -> PostgreSQL ou MongoDB
  -> JsonResponse
```

### Responsabilidade De Cada Camada

`views.py`

Recebe a requisicao HTTP, le JSON, chama schemas/services e retorna `JsonResponse`. Nao deve conter regra pesada de negocio nem acesso direto a banco.

`services.py`

Contem casos de uso, como criar, listar, atualizar e deletar produtos.

`repositories.py`

Contem classes que conversam com bancos de dados:

- `UserRepository`: usuarios no PostgreSQL via Django ORM.
- `ProductRepository`: produtos no MongoDB via PyMongo.

`schemas.py`

Valida dados de entrada e padroniza dados de saida.

`auth.py`

Gera e valida JWT, autentica usuario e recupera usuario atual pelo token.

`database.py`

Centraliza criacao e reutilizacao do cliente MongoDB.

`swagger.py`

Mantem a especificacao OpenAPI separada da view.

## Bancos De Dados

### PostgreSQL

Usado apenas para autenticacao e gerenciamento de usuarios.

Banco:

```text
think_auth
```

Tabelas principais criadas pelo Django:

```text
auth_user
auth_group
auth_permission
django_session
django_admin_log
django_content_type
```

Configuracao em:

```text
think_produto/settings.py
```

### MongoDB

Usado para produtos.

Banco:

```text
think_products
```

Colecao:

```text
products
```

Documento de produto:

```json
{
  "_id": "ObjectId",
  "nome": "Notebook",
  "descricao": "Notebook para desenvolvimento",
  "preco": 4500.9,
  "status": "ativo",
  "data_criacao": "2026-07-29T06:58:06.549000"
}
```

Na API, `_id` e convertido para `id`.

## Variaveis De Ambiente

Crie um arquivo `.env` com base em `.env.example`:

```bash
cp .env.example .env
```

Exemplo:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=think_auth
POSTGRES_USER=think_user
POSTGRES_PASSWORD=think_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

JWT_SECRET_KEY=change-me
JWT_ACCESS_TOKEN_EXPIRE_SECONDS=1800

MONGO_INITDB_ROOT_USERNAME=think_mongo_user
MONGO_INITDB_ROOT_PASSWORD=think_mongo_password
MONGO_DB=think_products
MONGO_URI=mongodb://think_mongo_user:think_mongo_password@127.0.0.1:27017/think_products?authSource=admin
```

## Como Rodar O Projeto

Entre na pasta do projeto Django:

```bash
cd /Users/gabrielruas/Desktop/Gabriel/1-Projetos/desafio_think/Projeto/think_produto
```

Suba os bancos:

```bash
docker compose up -d postgres mongo
```

Instale dependencias, se necessario:

```bash
../venv/bin/python -m pip install -r requirements.txt
```

Aplique migrations do Django no PostgreSQL:

```bash
../venv/bin/python manage.py migrate
```

Rode o servidor:

```bash
../venv/bin/python manage.py runserver 127.0.0.1:8000
```

Acesse:

```text
http://127.0.0.1:8000/
```

## Acessos

Pagina inicial:

```text
http://127.0.0.1:8000/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

Swagger:

```text
http://127.0.0.1:8000/swagger/
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

Usuario admin criado no ambiente local:

```text
username: gabriel
email: gabriel@email.com
senha: 123456
```

## Rotas De Autenticacao

### Registrar Usuario

```http
POST /auth/register
```

Body:

```json
{
  "username": "gabriel",
  "email": "gabriel@email.com",
  "password": "123456"
}
```

### Login

```http
POST /auth/login
```

Body com username:

```json
{
  "username": "gabriel",
  "password": "123456"
}
```

Body com email:

```json
{
  "email": "gabriel@email.com",
  "password": "123456"
}
```

Resposta:

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### Usuario Atual

```http
GET /auth/me
Authorization: Bearer <access_token>
```

## Rotas De Produtos

### Listar Produtos

```http
GET /products
```

Filtro opcional:

```http
GET /products?status=ativo
```

### Criar Produto

```http
POST /products
Authorization: Bearer <access_token>
```

Body:

```json
{
  "nome": "Notebook",
  "descricao": "Notebook para desenvolvimento",
  "preco": 4500.9,
  "status": "ativo"
}
```

### Buscar Produto Por ID

```http
GET /products/{product_id}
```

### Atualizar Produto Completo

```http
PUT /products/{product_id}
Authorization: Bearer <access_token>
```

Body:

```json
{
  "nome": "Notebook Pro",
  "descricao": "Notebook atualizado",
  "preco": 4999.99,
  "status": "ativo"
}
```

### Atualizar Produto Parcial

```http
PATCH /products/{product_id}
Authorization: Bearer <access_token>
```

Body:

```json
{
  "status": "inativo"
}
```

### Deletar Produto

```http
DELETE /products/{product_id}
Authorization: Bearer <access_token>
```

Resposta esperada:

```text
204 No Content
```

## Exemplos Com Curl

Login:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gabriel","password":"123456"}'
```

Criar produto:

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -d '{"nome":"Notebook","descricao":"Notebook para desenvolvimento","preco":4500.9,"status":"ativo"}'
```

Listar produtos:

```bash
curl http://127.0.0.1:8000/products
```

## Manutencao

### Adicionar Nova Rota

1. Adicione a URL em `produto/urls.py`.
2. Crie a funcao controller em `produto/views.py`.
3. Coloque validacao em `produto/schemas.py`.
4. Coloque regra de negocio em `produto/services.py`.
5. Coloque acesso ao banco em `produto/repositories.py`.
6. Atualize a documentacao em `produto/swagger.py`.

### Alterar Regra De Produto

Use principalmente:

```text
produto/schemas.py
produto/services.py
```

Exemplo: se um produto nao puder ter preco zero, a validacao deve ficar em `schemas.py` ou a regra em `services.py`, dependendo da regra.

### Alterar Estrutura Do Produto No MongoDB

Arquivos envolvidos:

```text
produto/schemas.py
produto/repositories.py
produto/swagger.py
docker/mongo/init.js
```

### Alterar Autenticacao/JWT

Arquivo principal:

```text
produto/auth.py
```

Configuracoes:

```text
JWT_SECRET_KEY
JWT_ACCESS_TOKEN_EXPIRE_SECONDS
```

### Alterar Banco PostgreSQL

Configuracao:

```text
think_produto/settings.py
```

Depois rode:

```bash
../venv/bin/python manage.py migrate
```

### Alterar Banco MongoDB

Configuracao:

```text
MONGO_URI
MONGO_DB
```

Provider:

```text
produto/database.py
```

## Testes Manuais Recomendados

Depois de qualquer mudanca importante, valide:

```bash
../venv/bin/python manage.py check
```

Fluxo minimo:

1. Abrir `/swagger/`.
2. Fazer login em `/auth/login`.
3. Usar o token no Swagger em Authorize.
4. Criar produto.
5. Listar produto.
6. Buscar produto por ID.
7. Atualizar produto.
8. Deletar produto.
9. Confirmar que buscar produto deletado retorna 404.

## Troubleshooting

### Porta 8000 Em Uso

Erro:

```text
Error: That port is already in use.
```

Solucao: pare o servidor antigo ou rode em outra porta:

```bash
../venv/bin/python manage.py runserver 127.0.0.1:8001
```

### `/auth/login` Retorna Method Not Allowed

Isso acontece ao abrir `/auth/login` no navegador. O navegador faz `GET`, mas a rota aceita apenas `POST`.

Use Swagger, Postman, Insomnia ou `curl`.

### Erro De Conexao Com PostgreSQL

Confirme se o container esta rodando:

```bash
docker compose ps postgres
```

Suba novamente:

```bash
docker compose up -d postgres
```

### Erro De Conexao Com MongoDB

Confirme se o container esta rodando:

```bash
docker compose ps mongo
```

Suba novamente:

```bash
docker compose up -d mongo
```

### Swagger Nao Carrega Visualmente

O HTML do Swagger usa arquivos via CDN:

```text
https://unpkg.com/swagger-ui-dist@5
```

Se estiver sem internet, o `/openapi.json` continua funcionando, mas a interface visual pode nao carregar.

## Estado Atual Da Aplicacao

Implementado:

- Django Admin.
- PostgreSQL para usuarios.
- JWT para API.
- MongoDB para produtos.
- CRUD completo de produtos.
- Swagger/OpenAPI.
- Organizacao com Design Patterns.

Pendencias recomendadas para evolucao:

- Criar testes automatizados com `pytest`.
- Separar configuracoes por ambiente.
- Usar biblioteca JWT dedicada, como PyJWT, se permitido.
- Criar permissao por perfil de usuario.
- Adicionar pagina administrativa customizada para produtos do MongoDB, se for necessario gerenciar produtos fora do Swagger.
