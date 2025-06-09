from typing import Dict, Type

from pms.utils.helpers import FnsPropertyHelper
from pms.utils.helpers.base import BasePropertyHelper
from properties.models import Property
from utils.SingletonMeta import SingletonMeta


class PMSHelperFactory(metaclass=SingletonMeta):
    _helpers: Dict[int, Type[BasePropertyHelper]] = {
        1: FnsPropertyHelper,
    }

    def get_helper(self, prop: Property) -> BasePropertyHelper:
        helper_class = self._helpers.get(prop.pms_id)
        if helper_class is None:
            raise ValueError(f"PMS ID {prop.pms_id} no soportado")
        return helper_class(prop)
