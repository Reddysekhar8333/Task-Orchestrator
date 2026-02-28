"""Django settings for task_manager project."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {'1', 'true', 'yes', 'on'}


def _load_keyvault_secrets(vault_name: str) -> dict[str, str]:
    """Load configured secrets from Azure Key Vault.

    If Key Vault is unavailable (local dev/Jenkins), return an empty dict and
    allow environment-variable fallbacks.
    """

    secret_mapping = {
        'DJANGO-SECRET-KEY': 'SECRET_KEY',
        'DB-NAME': 'DB_NAME',
        'DB-USER': 'DB_USER',
        'DB-PASS': 'DB_PASS',
        'DB-HOST': 'DB_HOST',
        'AZURE-ACCOUNT-NAME': 'AZURE_ACCOUNT_NAME',
        'AZURE-ACCOUNT-KEY': 'AZURE_ACCOUNT_KEY',
    }

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        client = SecretClient(
            vault_url=f'https://{vault_name}.vault.azure.net',
            credential=DefaultAzureCredential(),
        )

        loaded = {}
        for kv_name, local_name in secret_mapping.items():
            loaded[local_name] = client.get_secret(kv_name).value
        return loaded
    except Exception:
        return {}


VAULT_NAME = os.getenv('AZURE_VAULT_NAME')
VAULT_SECRETS = _load_keyvault_secrets(VAULT_NAME) if VAULT_NAME else {}

for key, value in VAULT_SECRETS.items():
    if value and not os.getenv(key):
        os.environ[key] = value

SECRET_KEY = VAULT_SECRETS.get('SECRET_KEY') or os.getenv('SECRET_KEY', 'default-insecure-key')
DEBUG = _get_env_bool('DEBUG', True)
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'users',
    'tasks',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'task_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'task_manager.wsgi.application'

if os.getenv('ENV') == 'PROD':
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': VAULT_SECRETS.get('DB_NAME') or os.getenv('DB_NAME'),
            'USER': VAULT_SECRETS.get('DB_USER') or os.getenv('DB_USER'),
            'PASSWORD': VAULT_SECRETS.get('DB_PASS') or os.getenv('DB_PASS'),
            'HOST': VAULT_SECRETS.get('DB_HOST') or os.getenv('DB_HOST'),
            'PORT': '1433',
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server',
                'extra_params': 'Encrypt=yes;TrustServerCertificate=no',
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

if (VAULT_SECRETS.get('AZURE_ACCOUNT_NAME') or os.getenv('AZURE_ACCOUNT_NAME')) and (
    VAULT_SECRETS.get('AZURE_ACCOUNT_KEY') or os.getenv('AZURE_ACCOUNT_KEY')
):
    DEFAULT_FILE_STORAGE = 'task_manager.custom_azure.AzureMediaStorage'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'