from datetime import datetime
from typing import List, Optional

from ninja import Schema


class RoomReservationOut(Schema):
    id: int
    room_type: str
    price: float
    guests: int

    @staticmethod
    def resolve_name(obj):
        return obj.room_type.name if obj.room_type else None


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


class RoomReservationSchema(Schema):
    room_type: str
    price: float
    guests: int


class ReservationClientOut(Schema):
    room_reservations: List[RoomReservationSchema]
    property: str
    check_in: datetime
    check_out: datetime
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
    pax_count: int
    total_price: float
    status: str

    @staticmethod
    def resolve_room_reservations(obj):
        return [
            {
                "room_type": rr.room_type.name,
                "price": rr.price,
                "guests": rr.guests,
            }
            for rr in obj.reservations.all()
        ]

    @staticmethod
    def resolve_property(obj):
        return obj.property.name if obj.property else None
