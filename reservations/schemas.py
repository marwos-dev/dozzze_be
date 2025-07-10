from datetime import datetime
from typing import Optional

from ninja import Schema


class RoomReservationOut(Schema):
    id: int
    name: str
    price: float
    guests: int

    @staticmethod
    def resolve_name(obj):
        return obj.room.name


class ReservationSchema(Schema):
    property_id: int
    channel: str
    pax_count: int
    currency: str
    room_type: str
    room_type_id: int
    total_price: float
    check_in: datetime
    check_out: datetime
    guest_corporate: Optional[str] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_address: Optional[str] = None
    guest_city: Optional[str] = None
    guest_country: Optional[str] = None
    guest_region: Optional[str] = None
    guest_country_iso: Optional[str] = None
    guest_cp: Optional[str] = None
    guest_remarks: Optional[str] = None
    cancellation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    paid_online: Optional[float] = None
    pay_on_arrival: Optional[float] = None


class RedsysSchemaOut(Schema):
    endpoint: str
    Ds_SignatureVersion: str
    Ds_MerchantParameters: str
    Ds_Signature: str


class ReservationOut(Schema):
    success: bool
    redsys_args: RedsysSchemaOut
