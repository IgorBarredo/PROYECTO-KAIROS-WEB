"""
Django settings for djangoProject project.

Modified for Production with:
- python-decouple (Seguridad de claves)
- WhiteNoise (Archivos estáticos/CSS)
- dj-database-url (Base de datos flexible)
"""

from pathlib import Path
import os
from decouple import config, Csv  # <-- Importante para leer el .env
import dj_database_url            # <-- Importante para la base de datos

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
#  SEGURIDAD Y CONFIGURACIÓN DEL ENTORNO
# ==============================================================================

# Lee la clave secreta del archivo .env (Si no la encuentra, da error para avisarte)
SECRET_KEY = config('SECRET_KEY')

# Lee DEBUG como True/False.
# En producción (.env del servidor) será False. En local (.env tuyo) puede ser True.
DEBUG = config('DEBUG', default=False, cast=bool)

# Lee la lista de hosts permitidos separada por comas desde el .env
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'appKairos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- AÑADIDO: Motor de CSS para producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'appKairos' / 'templates'],
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

WSGI_APPLICATION = 'djangoProject.wsgi.application'


# ==============================================================================
#  BASE DE DATOS (Híbrida: SQLite en local / PostgreSQL en nube)
# ==============================================================================

DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3')),
        conn_max_age=600
    )
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

# Logging básico
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_TZ = True


# ==============================================================================
#  ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES)
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Carpeta donde WhiteNoise recolectará todo

STATICFILES_DIRS = [
    BASE_DIR / 'appKairos' / 'static',
]

# Motor de almacenamiento de WhiteNoise con compresión (Hace que la web cargue rápido)
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'    # esta si falta un icono rompe la web
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'             #esta no rompe la web si falta un icono

# Media files (Archivos subidos por usuarios, si hubiera)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = 'appKairos.Usuario'
AUTHENTICATION_BACKENDS = [
    'appKairos.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Login/Logout
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'


# ==============================================================================
#  CONFIGURACIÓN DE EMAIL (SMTP REAL)
# ==============================================================================

# Lee la configuración del .env para no exponer contraseñas
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'noreply@proyectokairos.com'
CONTACT_EMAIL = 'contact@proyectokairos.com'

# Evitar el bucle de redirecciones en Render
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Seguridad adicional para Producción (Solo se activa si DEBUG es False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
