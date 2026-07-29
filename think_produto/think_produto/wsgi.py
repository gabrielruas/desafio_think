"""Configuracao WSGI do projeto think_produto."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'think_produto.settings')

application = get_wsgi_application()
