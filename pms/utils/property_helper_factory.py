"""Utilities to obtain the correct PMS helper for a property."""

import inspect
import pkgutil
from importlib import import_module
from typing import Dict, Type

from django.utils.text import slugify

from pms.utils.helpers import __name__ as helpers_pkg
from pms.utils.helpers import __path__ as helpers_path
from pms.utils.helpers.base import BasePropertyHelper
from properties.models import Property
from utils.SingletonMeta import SingletonMeta


class PMSHelperFactory(metaclass=SingletonMeta):
    """Factory that returns the helper class for a given ``Property``."""

    def __init__(self) -> None:
        self._helpers: Dict[str, Type[BasePropertyHelper]] = {}
        self._discover_helpers()

    def _discover_helpers(self) -> None:
        """Populate ``self._helpers`` discovering available helpers."""
        for _, module_name, ispkg in pkgutil.iter_modules(helpers_path):
            if ispkg:
                continue
            module = import_module(f"{helpers_pkg}.{module_name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BasePropertyHelper)
                    and obj is not BasePropertyHelper
                ):
                    key = getattr(obj, "pms_key", slugify(obj.__name__))
                    self._helpers[key] = obj

    def has_helper(self, key: str) -> bool:
        """Return ``True`` if a helper is registered for ``key``."""
        return key in self._helpers

    def get_helper(self, prop: Property) -> BasePropertyHelper:
        if prop.pms is None:
            raise ValueError("Property has no PMS associated")

        key = prop.pms.pms_key or slugify(prop.pms.name)
        helper_class = self._helpers.get(key)
        if helper_class is None:
            raise ValueError(f"PMS '{key}' no soportado")
        return helper_class(prop)
