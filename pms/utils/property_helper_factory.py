# from .FnsPropertyHelper import FnsPropertyHelper

PMS_HELPER_MAP = {
    # "fns": FnsPropertyHelper,
    # 'otro_pms': OtroPMSHelper,
}


def get_property_helper(pms_code: str):
    helper_class = PMS_HELPER_MAP.get(pms_code.lower())
    if not helper_class:
        raise ValueError(f"No helper class found for PMS: {pms_code}")
    return helper_class()
