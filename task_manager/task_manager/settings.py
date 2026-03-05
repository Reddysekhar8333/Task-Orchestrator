"""Django settings for task_manager project."""
import json
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

#  load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Load both possible project .env locations and give them precedence over
# inherited container/shell values so local configuration is honored.
for dotenv_path in (BASE_DIR.parent / '.env', BASE_DIR / '.env'):
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)


def _get_env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}

def _sanitize_host_entry(host: str) -> str:
    normalized = host.strip().strip("'\"")
    if not normalized:
        return ''
    # Allow explicit wildcard entries.
    if normalized == '*':
        return normalized
    # Normalize values accidentally provided as full URLs so they can still be
    # used as ALLOWED_HOSTS entries (e.g. http://example.com:8081/).
    if '://' in normalized:
        normalized = urlsplit(normalized).hostname or ''
        return normalized.strip()
    # Strip path/query fragments when hosts are pasted with a trailing route.
    normalized = normalized.split('/', 1)[0].split('?', 1)[0]
    # Remove host port if provided for IPv4 or hostnames.
    if ':' in normalized and not normalized.startswith('['):
        normalized = normalized.split(':', 1)[0]
    return normalized.strip()

def _get_allowed_hosts() -> list[str]:
    raw_value = os.getenv('ALLOWED_HOSTS', '')
    if not raw_value:
        return ['localhost', '127.0.0.1']
    # Support multiple formats commonly used in CI/CD credentials:
    # - "a.com,b.com"
    # - "a.com b.com"
    # - '["a.com", "b.com"]'
    raw_value = raw_value.strip()
    if raw_value.startswith('['):
        try:
            loaded_hosts = json.loads(raw_value)
            if isinstance(loaded_hosts, list):
                return [
                    sanitized_host
                    for host in loaded_hosts
                    if (sanitized_host := _sanitize_host_entry(str(host)))
                ]
        except json.JSONDecodeError:
            pass

    normalized_value = raw_value.replace(';', ',').replace('\n', ',').replace(' ', ',')
    return [
        sanitized_host
        for host in normalized_value.split(',')
        if (sanitized_host := _sanitize_host_entry(host))
    ]

ENV = os.getenv('ENV', 'PROD').upper()
SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-key')
DEBUG = _get_env_bool('DEBUG', ENV != 'PROD')
ALLOWED_HOSTS = _get_allowed_hosts()

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
    'storages',
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
        'DIRS': [BASE_DIR / 'templates'],
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

USE_AZURE_SQL = _get_env_bool('USE_AZURE_SQL', ENV == 'PROD')

azure_db_config = {
    'NAME': os.getenv('DB_NAME'),
    'USER': os.getenv('DB_USER'),
    'PASSWORD': os.getenv('DB_PASS') or os.getenv('DB_PASSWORD'),
    'HOST': os.getenv('DB_HOST'),
    'PORT': os.getenv('DB_PORT', '1433'),
}

required_azure_db_values = {'NAME', 'USER', 'PASSWORD', 'HOST'}
missing_azure_db_values = [
    key for key in required_azure_db_values if not azure_db_config.get(key)
]

if USE_AZURE_SQL and missing_azure_db_values:
    print(
        'USE_AZURE_SQL is enabled but missing database settings '
        f"({', '.join(sorted(missing_azure_db_values))}). Falling back to sqlite3."
    )
    USE_AZURE_SQL = False

if USE_AZURE_SQL:
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            **azure_db_config,
            'OPTIONS': {
                'driver': os.getenv('SQL_SERVER_DRIVER', 'ODBC Driver 18 for SQL Server'),
                'extra_params': os.getenv(
                    'SQL_SERVER_EXTRA_PARAMS',
                    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;',
                ),
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

AZURE_ACCOUNT_NAME = os.getenv('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_ACCOUNT_KEY')
AZURE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_MEDIA_CONTAINER = os.getenv('AZURE_MEDIA_CONTAINER', 'media')
AZURE_STATIC_CONTAINER = os.getenv('AZURE_STATIC_CONTAINER', 'static')

if AZURE_CONNECTION_STRING or (AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY):
    DEFAULT_FILE_STORAGE = 'task_manager.custom_azure.AzureMediaStorage'

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'