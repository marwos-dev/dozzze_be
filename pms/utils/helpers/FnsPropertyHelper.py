import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from typing import Dict, List, Union

from pms.utils.AuthApi import AuthApi
from pms.utils.base import BasePropertyHelper
from properties.models import Property


class FnsPropertyHelper(BasePropertyHelper):
    """Helper class for FNSROOMS operations"""

    def __init__(self, prop: Property):
        super().__init__(prop)
        self.api_auth = AuthApi()
        self.property = prop
        if hasattr(prop, "pms_data") and prop.pms_data:
            self.setup_api_client(prop)

    def setup_api_client(self, prop: Property = None):
        """Initialize the FNSROOMS API client"""
        if not prop:
            raise ValueError("Property must be provided to initialize API client.")

    def download_room_list(self, prop: Property):
        """
        Download the list of rooms from FNSROOMS.

        Args:
            prop: Property object containing PMS data.

        Returns:
            dict: A dictionary with room information.
        """
        try:
            api_call = self.api_auth.init_call(
                domain=prop.pms_data.base_url,
                authorization={"Cookie": prop.pms_data.pms_token},
            )
            params = {
                "pms_id": prop.pms.pms_external_id,
                "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                "user": prop.pms_data.pms_username,
                "password": prop.pms_data.pms_password,
                # "date_start": "2025-06-03",
                # "date_end": "2025-06-03",
            }

            response = api_call._get(url="/getRoomList.php", params=params)
            return self._parse_room_list(response)
        except Exception as e:
            print(f"Error downloading getRoomList: {e}")
            return {}

    def download_reservations(self, prop: Property):
        """
        Download reservations from FNSROOMS.

        Args:
            prop: Property object containing PMS data.

        Returns:
            dict: A dictionary with reservation details.
        """
        try:
            api_call = self.api_auth.init_call(
                domain=prop.pms_data.base_url,
                authorization={"Cookie": prop.pms_data.pms_token},
            )
            response = api_call._get(
                url="/getHotelBookingsJSON.php",
                params={
                    "pms_id": prop.pms.pms_external_id,
                    "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                    "user": prop.pms_data.pms_username,
                    "password": prop.pms_data.pms_password,
                    "date_start": date(2025, 6, 1).strftime("%Y-%m-%d"),
                    "date_end": date(2025, 6, 29).strftime("%Y-%m-%d"),
                },
            )
            return self._parse_reservations(response)
        except Exception as e:
            print(f"Error downloading getReservations: {e}")
            return {}

    def download_property_details(self, prop: Property):
        """
        Download property details from FNSROOMS.

        Args:
            prop: Property object containing PMS data.

        Returns:
            dict: A dictionary with property details.
        """
        try:
            api_call = self.api_auth.init_call(
                domain=prop.pms_data.base_url,
                authorization={"Cookie": prop.pms_data.pms_token},
            )
            response = api_call._get(
                url="/getProperties.php",
                params={
                    "pms_id": prop.pms.pms_external_id,
                    "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                    "user": prop.pms_data.pms_username,
                    "password": prop.pms_data.pms_password,
                },
            )
            return self._parse_property_details(response)
        except Exception as e:
            print(f"Error downloading getPropertyDetails: {e}")
            return {}

    def download_availability(self, prop: Property):
        try:
            api_call = self.api_auth.init_call(domain=prop.pms_data.base_url)
            params = self._build_request_params(prop)

            availability_response = api_call._get(
                url="/getAvailabilityRevenue.php", params=params
            )

            return self._parse_availability(
                xml_string_availability=availability_response
            )
        except Exception as e:
            print(f"Error downloading getAvailabilityRevenue: {e}")
            return {}

    def _build_request_params(self, prop: Property):
        """
        Build the request parameters for the FNSROOMS API.

        Args:
            prop (dict): Property information.
            start_date_id (int): Start date ID.
            end_date_id (int): End date ID.

        Returns:
            dict: Request parameters for the API call.
        """
        # start_date = replace_day(get_ddate_text(start_date_id))
        # end_date = get_ddate_text(end_date_id)

        return {
            "pms_id": prop.pms_data.pms_token,
            "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
            "user": prop.pms_data.pms_username,
            "password": prop.pms_data.pms_password,
            "start_date": date(2025, 1, 1).strftime("%Y-%m-%d"),  # Example start date
            "end_date": date(2025, 12, 31).strftime("%Y-%m-%d"),  # Example end date
            "currency": "EUR",
        }

    def _parse_room_list(self, xml_string: str):
        # Parseamos el XML
        root = ET.fromstring(xml_string)

        # Extraemos los datos
        rooms = defaultdict(list)

        for room in root.findall(".//room"):
            room_data = {
                "external_id": int(room.findtext("id")),
                "name": room.findtext("nombre"),
                "external_room_type_id": int(room.findtext("tipo_habitacion_id")),
                "external_room_type_name": room.findtext("tipo_habitacion_nombre"),
            }
            rooms[room_data["external_room_type_id"]].append(room_data)

        return dict(rooms)

    def _parse_property_details(self, xml_string: str) -> Dict[str, str]:
        root = ET.fromstring(xml_string)

        property_el = root.find(".//property")
        if property_el is None:
            return None

        data = {
            "pms_property_id": property_el.findtext("id"),
            "pms_property_name": property_el.findtext("name").strip(),
            "pms_property_address": property_el.find(
                "address/component[@name='addr1']"
            ).text.strip(),
            "pms_property_city": property_el.find(
                "address/component[@name='city']"
            ).text.strip(),
            "pms_property_province": property_el.find(
                "address/component[@name='province']"
            ).text.strip(),
            "pms_property_postal_code": property_el.find(
                "address/component[@name='postal_code']"
            ).text.strip(),
            "pms_property_country": property_el.findtext("country"),
            "pms_property_latitude": float(property_el.findtext("latitude")),
            "pms_property_longitude": float(property_el.findtext("longitude")),
            "pms_property_phone": property_el.findtext("phone"),
            "pms_property_category": property_el.findtext("category").strip().lower(),
        }

        return data

    def _parse_reservations(self, response) -> List[Dict[str, Union[str, Dict]]]:
        reservations = []

        if "bookings" in response or "booking" in response["bookings"]:
            for booking in response["bookings"]["booking"]:
                reservation_data = {
                    "reservation_id": booking.get("reservation_id"),
                    "alojamiento_id": booking.get("alojamiento_id"),
                    "localizador": booking.get("localizador"),
                    "channel": booking.get("channel"),
                    "channel_id": booking.get("channel_id"),
                    "status": booking.get("status"),
                    "check_in": booking.get("date_arrival"),
                    "check_out": booking.get("date_departure"),
                    "creation_date": booking.get("creation_date"),
                    "cancellation_date": (
                        booking.get("cancellation_date")
                        if booking.get("cancellation_date")
                        else None
                    ),
                    "modification_date": (
                        booking.get("modification_date")
                        if booking.get("modification_date")
                           and "0000" not in booking.get("modification_date")
                        else None
                    ),
                    "currency": booking.get("currency"),
                    "paid_online": booking.get("paid_online"),
                    "pay_on_arrival": booking.get("pay_on_arrival"),
                    "total_price": booking.get("total_price"),
                    "client_corporate": booking.get("client_corporate"),
                    "guest_name": (
                        booking.get("client_name")
                        if booking.get("client_name")
                        else booking.get("client_firstname")
                    ),
                    "guest_email": (
                        booking.get("client_email")
                        if booking.get("client_email")
                        else booking.get("client_mail")
                    ),
                    "guest_phone": (
                        booking.get("client_telephone")
                        if booking.get("client_telephone")
                        else booking.get("client_phone")
                    ),
                    "guest_address": (
                        booking.get("client_address")
                        if booking.get("client_address")
                        else booking.get("client_street")
                    ),
                    "guest_city": (
                        booking.get("client_city")
                        if booking.get("client_city")
                        else booking.get("client_locality")
                    ),
                    "guest_region": (
                        booking.get("client_region")
                        if booking.get("client_region")
                        else booking.get("client_province")
                    ),
                    "guest_country": (
                        booking.get("client_country")
                        if booking.get("client_country")
                        else booking.get("client_country_name")
                    ),
                    "guest_country_iso": (
                        booking.get("client_countryiso")
                        if booking.get("client_countryiso")
                        else booking.get("client_country_code")
                    ),
                    "guest_cp": (
                        booking.get("client_cp")
                        if booking.get("client_cp")
                        else booking.get("client_city")
                    ),
                    "guest_remarks": (
                        booking.get("client_remarks")
                        if booking.get("client_remarks")
                        else booking.get("client_observations")
                    ),
                }
                rooms = []
                for room in booking["rooms"]:
                    if room.get("arrayHabitacion", []):
                        for sub_room in room["arrayHabitacion"]:
                            rooms.append(
                                {
                                    "external_id": sub_room.get("habitacion_id"),
                                    "room_type_id": room.get("room_type_id"),
                                    "rate_id": room.get("rate_id"),
                                    "client_name": "",
                                }
                            )
                    else:
                        rooms.append(
                            {
                                "room_type_id": room.get("room_type_id"),
                                "rate_id": room.get("rate_id"),
                                "occupancy": room.get("occupancy"),
                            }
                        )

                if len(rooms) == 1:
                    reservation_data["rooms"] = rooms[0]
                else:
                    reservation_data["rooms"] = rooms

                reservations.append(reservation_data)

        return reservations
