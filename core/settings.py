"""
Django settings for KisanBazaar V2.0
======================================

Environment variables are loaded from a .env file in BASE_DIR.
Create one by copying .env.example:

    cp .env.example .env

Required .env keys:
    SECRET_KEY=<strong-random-string>
    DEBUG=True
    GEMINI_API_KEY=<your-google-gemini-key>   # https://aistudio.google.com/app/apikey

Optional .env keys:
    ALLOWED_HOSTS=localhost,127.0.0.1
    DATABASE_URL=sqlite:///db.sqlite3

Install dependencies:
    pip install django pillow python-dotenv
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load the secret vault
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Securely pull your API key into Django
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ── python-dotenv: load .env if present (silently ignored if absent) ─────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass   # python-dotenv not installed; fall back to os.environ only

# ── Base directory ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ══════════════════════════════════════════════════════════════════════════════
#  CORE SECURITY
# ══════════════════════════════════════════════════════════════════════════════

# SECURITY WARNING: keep the secret key used in production secret!
# Set a strong value in .env for production; the insecure default is dev-only.
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-kisanbazaar-v2-dev-only-CHANGE-IN-PRODUCTION",
)

# SECURITY WARNING: never run with DEBUG=True in production!
DEBUG = os.environ.get("DEBUG", "True").strip().lower() in ("true", "1", "yes")

_raw_hosts = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]


# ── Production hardening (auto-disabled when DEBUG=True) ─────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER        = True
    SECURE_CONTENT_TYPE_NOSNIFF      = True
    SECURE_HSTS_SECONDS              = 31_536_000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
    SECURE_SSL_REDIRECT              = True
    SESSION_COOKIE_SECURE            = True
    CSRF_COOKIE_SECURE               = True
    X_FRAME_OPTIONS                  = "DENY"


# ══════════════════════════════════════════════════════════════════════════════
#  AI / THIRD-PARTY KEYS  — read from environment, NEVER hardcoded
# ══════════════════════════════════════════════════════════════════════════════

# Google Gemini API key — powers ROI Predictor and Kisan Mitra chatbot.
# Leave empty to run without AI features (graceful degradation is built-in).
# Get a free key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# ══════════════════════════════════════════════════════════════════════════════
#  INSTALLED APPS
# ══════════════════════════════════════════════════════════════════════════════

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "marketplace",
]


# ══════════════════════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ══════════════════════════════════════════════════════════════════════════════

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"


# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],          # APP_DIRS=True handles marketplace/templates/
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════════════════

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

AUTH_USER_MODEL    = "marketplace.User"
LOGIN_URL          = "/login/"
LOGIN_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNATIONALISATION
# ══════════════════════════════════════════════════════════════════════════════

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"   # IST — critical for correct expiry date math
USE_I18N      = True
USE_TZ        = True


# ══════════════════════════════════════════════════════════════════════════════
#  STATIC & MEDIA FILES
# ══════════════════════════════════════════════════════════════════════════════

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # used by collectstatic

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"          # uploaded crop photos


# ══════════════════════════════════════════════════════════════════════════════
#  MISC
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_AGE = 1_209_600   # 2 weeks — convenient on shared mobile devices