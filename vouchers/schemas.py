from typing import Optional

from ninja import Schema


class CodeValidationOut(Schema):
    type: str
    applicable: bool
    redemptions: Optional[int] = None
    remaining_amount: Optional[float] = None
    name: Optional[str] = None
    discount_percent: Optional[float] = None
