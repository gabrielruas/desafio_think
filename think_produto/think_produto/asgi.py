"""Configuracao ASGI do projeto think_produto."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'think_produto.settings')

application = get_asgi_application()
