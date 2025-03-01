from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m^*uy=+8g_08f$j2dj%-+t-zmx%=tq3u!_6^bh+vlhsi8sm^5_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '192.168.100.87',
    '10.31.3.28', 
    'localhost', 
    '127.0.0.1', 
    '192.168.100.116', 
    '10.31.3.11',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  
    'rest_framework',
    'django_filters',
    'corsheaders',
    'rest_framework_simplejwt',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.common.CommonMiddleware',

    # 'django.middleware.csrf.CsrfViewMiddleware',  // desabilitado para testes
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'manutencar_api.urls'

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

WSGI_APPLICATION = 'manutencar_api.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  
        'NAME': "banco_manutencar",                     
        'USER': "postgres",                  
        'PASSWORD': "postgres",             
        'HOST': 'localhost',                         
        'PORT': '5432',                             
    }
}

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Manaus'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.Usuario' 

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',  # Angular
    "http://localhost:8000",  # Django
    "http://127.0.0.1:8000",  # Django
    "http://localhost:3000",    # React
    "http://192.168.100.87:8000", # Ip de casa
    "http://10.31.3.28:8000", # ip escola
    "http://192.168.100.116:39875", # ip Celular casa
    "http://10.31.3.11:46331", # Celular ip escola
]

CORS_ALLOW_ALL_ORIGINS = True  # Libera acesso de qualquer origem
CORS_ALLOW_CREDENTIALS = True  # Permite credenciais
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
] # Métodos permitidos

CSRF_TRUSTED_ORIGINS = [
    "http://192.168.100.87:8000",
    "http://localhost:4200",
    "http://10.31.3.28:8000",
    
]  # Libera CSRF para essa URL

CORS_ALLOW_HEADERS = [
    'Authorization',
    'content-type',
    'accept',
    'origin',
    'x-csrftoken',
    'x-requested-with',
    'x-www-form-urlencoded',
] # Headers permitidos


CSRF_COOKIE_SECURE = False
CORS_ALLOW_CREDENTIALS = True

# JWT Authentication settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Suporte para autenticação baseada em sessão
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',  # Paginação
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',  # Filtros
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),   # 1 dia
    'ROTATE_REFRESH_TOKENS': True,  # Gera novos tokens ao usar refresh
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist para tokens antigos
}


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seuemail@gmail.com'
EMAIL_HOST_PASSWORD = 'suasenha'
