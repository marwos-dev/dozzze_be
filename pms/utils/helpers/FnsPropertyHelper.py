import calendar
import json
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Union

from pms.models import PMSDataResponse
from pms.utils.AuthApi import AuthApi
from pms.utils.helpers.base import BasePropertyHelper
from properties.models import Property


class FnsPropertyHelper(BasePropertyHelper):
    """Helper class for FNS Rooms PMS integration."""

    def __init__(self, prop: Property):
        super().__init__(prop)
        self.api_auth = AuthApi()
        self.property = prop
        if hasattr(prop, "pms_data"):
            try:
                if prop.pms_data:
                    self.setup_api_client(prop)
            except Exception:
                # PMS data might not exist during tests or initial setup
                pass

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
            }
            return self._parse_room_list(
                api_call._get(url="/getRoomList.php", params=params)
            )
        except Exception as e:
            print(f"Error downloading getRoomList: {e}")
            return {}

    def download_reservations(self, prop: Property, checkin=None, checkout=None):
        """
        Download reservations from FNSROOMS.

        Args:
            prop: Property object containing PMS data.
            checkin: Checkin date
            checkout: Checkout date

        Returns:
            dict: A dictionary with reservation details.
        """
        try:
            api_call = self.api_auth.init_call(
                domain=prop.pms_data.base_url,
                authorization={"Cookie": prop.pms_data.pms_token},
            )
            today = date.today()
            all_reservations = []
            if checkin and checkout:
                # Si se pasan fechas de checkin y checkout, descargamos solo ese rango
                first_day = checkin
                last_day = checkout
                all_reservations = self._get_reservations_for_range(
                    first_day, last_day, api_call, prop
                )
            elif prop.pms_data.first_sync and not checkin and not checkout:
                # Hacer una request por cada mes del año actual
                for month in range(today.month, today.month + 1):
                    first_day = date(today.year, month, 1)
                    last_day = date(
                        today.year, month, calendar.monthrange(today.year, month)[1]
                    )
                    monthly_reservations = self._get_reservations_for_range(
                        first_day, last_day, api_call, prop
                    )
                    all_reservations.extend(monthly_reservations)
                    time.sleep(2)
                prop.pms_data.first_sync = False
                prop.pms_data.save()
            else:
                # Solo el mes actual
                first_day = date(today.year, today.month, 1)
                last_day = date(
                    today.year,
                    today.month,
                    calendar.monthrange(today.year, today.month)[1],
                )
                all_reservations = self._get_reservations_for_range(
                    first_day, last_day, api_call, prop
                )
            PMSDataResponse.objects.create(
                pms=prop.pms,
                property=prop,
                function_name="download_reservations",
                response_data=json.dumps(all_reservations),
            )
            return all_reservations
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

    def download_availability(self, prop):
        try:
            apr = self.api_auth.init_call(
                domain=prop.base_url, authorization={"Cookie": prop.pms_data.pms_token}
            )

            availability_response = apr._get(
                url="/getAvailabilityRevenue.php",
                params={
                    "pms_id": prop.pms.pms_external_id,
                    "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                    "user": prop.pms_data.pms_username,
                    "password": prop.pms_data.pms_password,
                },
            )
            availability = self._parse_availability(
                xml_string_availability=availability_response
            )
            PMSDataResponse.objects.create(
                pms=prop.pms,
                property=prop,
                function_name="download_availability",
                response_data=json.dumps(availability),
            )
            return availability
        except Exception as e:
            print(f"Error downloading getAvailability: {e}")
            return {}

    def download_rates_and_availability(
        self, prop: Property, checkin=None, checkout=None
    ):
        """
        Download rates and availability from FNSROOMS.

        Args:
            prop: Property object containing PMS data.
            checkin: Checkin date (optional).
            checkout: Checkout date (optional).

        Returns:
            dict: A dictionary with rates and availability.
        """
        try:
            if not prop.pms_data:
                print(
                    f"Property {prop.name} does not have PMS data. "
                    "Skipping download of rates and availability."
                )
                return []

            api_call = self.api_auth.init_call(
                domain=prop.pms_data.base_url,
                authorization={"Cookie": prop.pms_data.pms_token},
            )
            all_rates = []
            today = date.today()
            start_date = None
            end_date = None
            if checkin and checkout:
                # If checkin and checkout dates are provided, download only that range
                start_date = checkin
                end_date = checkout
                all_rates = self._get_rates_and_availability_for_range(
                    start_date, end_date, api_call, prop
                )
            else:
                for month in range(today.month, today.month + 1):
                    if start_date is None:
                        start_date = date(today.year, month, 1)

                    first_day = date(today.year, month, 1)
                    last_day = date(
                        today.year, month, calendar.monthrange(today.year, month)[1]
                    )
                    monthly_rates = self._get_rates_and_availability_for_range(
                        first_day, last_day, api_call, prop
                    )
                    end_date = last_day
                    all_rates.extend(monthly_rates)
                    time.sleep(2)

            PMSDataResponse.objects.create(
                pms=prop.pms,
                property=prop,
                function_name="download_rates_and_availability",
                response_data=json.dumps(all_rates),
                start_date=start_date,
                end_date=end_date,
            )
            return all_rates
        except Exception as e:
            print(f"Error downloading getRates: {e}")
            return {}

    # PARSE METHODS
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

        property = root.find(".//property")
        if property is None:
            return None

        data = {
            "pms_property_id": property.findtext("id"),
            "pms_property_name": property.findtext("name").strip(),
            "pms_property_address": property.find(
                "address/component[@name='addr1']"
            ).text.strip(),
            "pms_property_city": property.find(
                "address/component[@name='city']"
            ).text.strip(),
            "pms_property_province": property.find(
                "address/component[@name='province']"
            ).text.strip(),
            "pms_property_postal_code": property.find(
                "address/component[@name='postal_code']"
            ).text.strip(),
            "pms_property_country": property.findtext("country"),
            "pms_property_latitude": float(property.findtext("latitude")),
            "pms_property_longitude": float(property.findtext("longitude")),
            "pms_property_phone": property.findtext("phone"),
            "pms_property_category": property.findtext("category").strip().lower(),
        }

        return data

    def _get_reservations_for_range(
        self, start_date, end_date, api_call, prop: Property
    ):
        response = api_call._get(
            url="/getHotelBookingsJSON.php",
            params={
                "pms_id": prop.pms.pms_external_id,
                "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                "user": prop.pms_data.pms_username,
                "password": prop.pms_data.pms_password,
                "date_start": start_date.strftime("%Y-%m-%d"),
                "date_end": end_date.strftime("%Y-%m-%d"),
            },
        )
        return self._parse_reservations(response, start_date, end_date, prop)

    def _get_rates_and_availability_for_range(
        self, start_date, end_date, api_call, prop: Property
    ):
        response = api_call._get(
            url="/getRates.php",
            params={
                "pms_id": prop.pms.pms_external_id,
                "hotel_pms_id": prop.pms_data.pms_hotel_identifier,
                "user": prop.pms_data.pms_username,
                "password": prop.pms_data.pms_password,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        )
        return self._parse_rates_and_availability(response)

    def _parse_reservations(
        self, response, start_date: datetime, end_date: datetime, prop: Property
    ) -> List[Dict[str, Union[str, Dict]]]:
        reservations = []

        if "bookings" in response or "booking" in response["bookings"]:
            if not response["bookings"]["booking"]:
                print(
                    f"No Hay reservas para la propiedar {prop.name} para "
                    f"el rango de fechas {start_date.strftime('%Y-%m-%d')} -"
                    f" {end_date.strftime('%Y-%m-%d')}"
                )
                return []

            for booking in response["bookings"]["booking"]:
                reservation_data = {
                    "reservation_id": booking.get("reservation_id"),
                    "alojamiento_id": booking.get("alojamiento_id"),
                    "property_id": prop.id,
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
                    "paid_online": float(booking.get("paid_online")),
                    "pay_on_arrival": float(booking.get("pay_on_arrival")),
                    "total_price": float(booking.get("total_price")),
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

                reservation_data["rooms"] = rooms
                reservations.append(reservation_data)

        return reservations

    def _parse_availability(self, xml_string_availability):
        # Parse the XML
        try:
            # TODO revisar los caracteres especiales
            xml_string = xml_string_availability.replace("&", " ")
            root = ET.fromstring(xml_string)

            result = {}

            # Iterate through the XML structure
            for revenue in root.findall("hotelRevenues/revenue"):
                for th in revenue.findall("th"):
                    roomTypeID = th.find("roomTypeID").text
                    date = th.find("day").text
                    # Convert the date to YYYY-MM-DD format
                    formatted_date = "-".join(reversed(date.split("/")))

                    # Compute the value as totalRooms - occupancy
                    totalRooms = int(th.find("totalRooms").text)
                    occupancy = int(th.find("occupancy").text)
                    value = totalRooms - occupancy

                    # Update the dictionary
                    if roomTypeID not in result:
                        result[roomTypeID] = {}
                    result[roomTypeID][formatted_date] = value

            result["total"] = result.pop("0")
            return result
        except Exception as e:
            print(f"Error parsing availability XML: {e}")
            return {}

    def _parse_rates_and_availability(self, xml_string: str):
        root = ET.fromstring(xml_string)
        if root is None:
            print("No data found in the XML response.")
            return []

        parsed_data = []

        for day in root.findall("dayAvailibityRoomType"):

            room_data = {
                "room_type": day.findtext("roomType"),
                "availability": int(day.findtext("availability")),
                "date": day.findtext("date"),
                "rates": [],
            }

            rates = day.find("rates")
            if not rates:
                continue

            for rate in day.find("rates").findall("rate"):
                rate_data = {
                    "rate_id": rate.findtext("rate_id"),
                    "prices": [],
                    "restrictions": {},
                }

                prices = rate.find("prices")
                if prices is not None:
                    for p in prices.findall("priceOccupancy"):
                        rate_data["prices"].append(
                            {
                                "occupancy": int(p.findtext("occupancy")),
                                "price": float(p.findtext("price")),
                            }
                        )

                restrictions = rate.find("restrictions")
                if restrictions is not None:
                    for r in restrictions:
                        rate_data["restrictions"][r.tag] = int(r.text)

                room_data["rates"].append(rate_data)

            parsed_data.append(room_data)
        return parsed_data
