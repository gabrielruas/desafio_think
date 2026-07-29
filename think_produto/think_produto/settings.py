"""Configuracoes do Django para o projeto think_produto."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Monta caminhos internos do projeto usando BASE_DIR / 'subpasta'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


# Configuracoes iniciais de desenvolvimento. Revise antes de usar em producao.

# Atencao: mantenha a chave secreta de producao fora do codigo-fonte.
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-0jn1$)x+-+i&x#n51wp*8@(7$8*+6gwe8f+9y6+zwilyo1%#ht',
)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_SECONDS', '1800'))
MONGO_URI = os.getenv(
    'MONGO_URI',
    'mongodb://think_mongo_user:think_mongo_password@127.0.0.1:27017/think_products?authSource=admin',
)
MONGO_DB = os.getenv('MONGO_DB', 'think_products')

# Atencao: nunca rode producao com DEBUG=True.
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Aplicacoes habilitadas no Django.

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'produto',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'think_produto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'think_produto.wsgi.application'


# Banco relacional usado pelo Django Auth e pelo Django Admin.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'think_auth'),
        'USER': os.getenv('POSTGRES_USER', 'think_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'think_password'),
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}


# Validadores de senha usados pelo sistema de usuarios do Django.

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internacionalizacao.

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Arquivos estaticos, como CSS, JavaScript e imagens.

STATIC_URL = 'static/'
