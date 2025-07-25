# myproject/__init__.py
from django.contrib import admin

from core.celery import app as celery_app


def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = _superuser_only.__get__(admin.site, type(admin.site))

__all__ = ("celery_app",)
