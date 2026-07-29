"""Rotas principais do projeto think_produto."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # O Django Admin gerencia usuarios, grupos e permissoes no PostgreSQL.
    path('admin/', admin.site.urls),
    # As rotas da API ficam no app produto.
    path('', include('produto.urls')),
]
