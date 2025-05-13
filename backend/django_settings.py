# backend/django_settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-key-change-me"
DEBUG = True

INSTALLED_APPS = [
    "backend.core",          # your app that contains models.py
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
