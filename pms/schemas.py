from typing import Optional

from ninja import Schema


class PMSOut(Schema):
    """Schema for PMS output"""

    id: int
    name: str
    pms_key: str
    pms_external_id: Optional[str] = None
    has_integration: bool
    description: Optional[str] = None
