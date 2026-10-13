"""Ajustes de VTON Studio. Todo lo sensible llega por variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
    if o.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "tryon",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "tryon.middleware.AccessLogMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de datos: PostgreSQL (pod aparte) si hay POSTGRES_HOST; si no, SQLite ---
DATA_DIR = Path(env("DATA_DIR", str(BASE_DIR / "data")))
if env("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", "vtonweb"),
            "USER": env("POSTGRES_USER", "vtonweb"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DATA_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = env("TIME_ZONE", "America/El_Salvador")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Las imágenes NO se sirven por URL pública: pasan por una vista que comprueba el dueño.
MEDIA_ROOT = Path(env("MEDIA_ROOT", str(DATA_DIR / "media")))
MEDIA_URL = "/private-media/"
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "studio"
LOGOUT_REDIRECT_URL = "home"

# --- Conexión con la API de IA (vton-api) y cola ---
VTON_API_URL = env("VTON_API_URL", "http://127.0.0.1:8000").rstrip("/")
VTON_API_KEY = env("VTON_API_KEY", "")
VTON_API_TIMEOUT = int(env("VTON_API_TIMEOUT", "300"))
VTON_STEPS = int(env("VTON_STEPS", "30"))
MAX_ACTIVE_JOBS_PER_USER = int(env("MAX_ACTIVE_JOBS_PER_USER", "3"))
JOB_MAX_ATTEMPTS = int(env("JOB_MAX_ATTEMPTS", "3"))
WORKER_POLL_SECONDS = float(env("WORKER_POLL_SECONDS", "2"))
MAX_UPLOAD_MB = int(env("MAX_UPLOAD_MB", "10"))

# Sin TLS todavía (Fase H): cookies sin Secure. Activar con DJANGO_HTTPS=1 cuando haya TLS.
if env("DJANGO_HTTPS", "0") == "1":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
