# import xml.etree.ElementTree as ET
# from collections import defaultdict
# from datetime import datetime, timedelta
# from typing import Dict
#
# from src.utils.func_utils import get_ddate_text, replace_day
#
# from .AuthApi import AuthApi
# from .base import BasePropertyHelper
#
#
# class FnsPropertyHelper(BasePropertyHelper):
#     """Helper class for FNSROOMS operations"""
#
#     def setup_api_client(self):
#         """Initialize the FNSROOMS API client"""
#         self.bApi = AuthApi()
#
#     def download_blocked(self, prop, start_date_id, end_date_id):
#         try:
#             apr = self.bApi.init_call(domain=prop.base_url)
#             params = self._build_request_params(prop, start_date_id, end_date_id)
#             response = apr._get(url="/getRoomBlockedJSON.php", params=params)
#             return self._parse_room_booked(
#                 response, params.get("start_date"), params.get("end_date")
#             )
#         except Exception as e:
#             # grLogger.error(f"Error downloading getAvailabilityRevenue: {e}")
#             return {}
#
#     def download_availability(self, prop, start_date_id, end_date_id):
#         try:
#             apr = self.bApi.init_call(domain=prop.base_url)
#             params = self._build_request_params(prop, start_date_id, end_date_id)
#
#             availability_response = apr._get(
#                 url="/getAvailabilityRevenue.php", params=params
#             )
#
#             return self._parse_availability(
#                 xml_string_availability=availability_response
#             )
#         except Exception as e:
#             # grLogger.error(f"Error downloading getAvailabilityRevenue: {e}")
#             return {}
#
#     def download_revenue(self, prop, start_date_id, end_date_id):
#         """
#         Get revenue from fns.
#
#         Args:
#             prop: dict, property information.
#             start_date: datetime or str, optional, start date for revenue data.
#             Defaults to the first of the current month.
#             end_date: datetime or str, optional, end date for revenue data.
#             Defaults to 90 days after today.
#
#         Returns:
#             dict: Revenue information.
#         """
#         start_date = replace_day(get_ddate_text(start_date_id))
#         end_date = get_ddate_text(end_date_id)
#         # Preparar los parámetros para la llamada a la API
#         apr = self.bApi.init_call(domain=prop.base_url)
#
#         # Preparing parameters for API call
#         params = {
#             "pms_id": prop.pms_token,
#             "hotel_pms_id": prop.pms_hotel_identifier,
#             "user": prop.pms_username,
#             "password": prop.pms_password,
#             "start_date": start_date,
#             # Ensuring first day of start_date's month
#             "end_date": end_date,
#             "currency": "EUR",
#         }
#
#         response = apr._get(url="/getProduction.php", params=params)
#         return self._parse_production(xml_string=response)
#
#     def update_prices(self, property, prices):
#         if not (property and prices):
#             return False
#
#         room_data = self._organize_price_data(prices)
#         schema = self._create_price_schema(room_data)
#         return self._send_prices_to_pms(property, schema)
#
#     def _build_request_params(self, prop, start_date_id, end_date_id):
#         """
#         Build the request parameters for the FNSROOMS API.
#
#         Args:
#             prop (dict): Property information.
#             start_date_id (int): Start date ID.
#             end_date_id (int): End date ID.
#
#         Returns:
#             dict: Request parameters for the API call.
#         """
#         start_date = replace_day(get_ddate_text(start_date_id))
#         end_date = get_ddate_text(end_date_id)
#
#         return {
#             "pms_id": prop.pms_token,
#             "hotel_pms_id": prop.pms_hotel_identifier,
#             "user": prop.pms_username,
#             "password": prop.pms_password,
#             "start_date": start_date,
#             "end_date": end_date,
#             "currency": "EUR",
#         }
#
#     def _parse_room_booked(self, response, start_date_str=None, end_date_str=None):
#         """
#         Parse room blocked data from JSON response.
#
#         Args:
#             response (dict): JSON response from the API (already parsed)
#             start_date_str (str, optional): Start date to filter results (format: YYYY-MM-DD)
#             end_date_str (str, optional): End date to filter results (format: YYYY-MM-DD)
#
#         Returns:
#             dict: Parsed room blocked data grouped by space_subtype_id (th)
#                  Each th has a dictionary of blocked rooms by date
#         """
#         try:
#
#             # Initialize the result dictionary
#             result = defaultdict(dict)
#
#             # Convert filter dates to datetime objects if provided
#             filter_start_date = (
#                 datetime.strptime(start_date_str, "%Y-%m-%d")
#                 if start_date_str
#                 else None
#             )
#             filter_end_date = (
#                 datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
#             )
#
#             # Check if the expected structure exists
#             if "roomsBlocked" in response and "room" in response["roomsBlocked"]:
#                 # Iterate through each room entry
#                 for room in response["roomsBlocked"]["room"]:
#                     # Extract the space_subtype_id (th field)
#                     space_subtype_id = room.get("th")
#
#                     if not space_subtype_id:
#                         continue
#
#                     # Get room block start and end dates
#                     room_start_date_str = room.get("fecha_inicio")
#                     room_end_date_str = room.get("fecha_fin")
#
#                     if not room_start_date_str or not room_end_date_str:
#                         continue
#
#                     # Convert strings to datetime objects
#                     room_start_date = datetime.strptime(room_start_date_str, "%Y-%m-%d")
#                     room_end_date = datetime.strptime(room_end_date_str, "%Y-%m-%d")
#
#                     # Apply date filters if provided
#                     effective_start_date = (
#                         max(room_start_date, filter_start_date)
#                         if filter_start_date
#                         else room_start_date
#                     )
#                     effective_end_date = (
#                         min(room_end_date, filter_end_date)
#                         if filter_end_date
#                         else room_end_date
#                     )
#
#                     # Skip if the room block is entirely outside our filter range
#                     if effective_start_date > effective_end_date:
#                         continue
#
#                     # Generate all dates in the range
#                     current_date = effective_start_date
#                     while current_date <= effective_end_date:
#                         date_str = current_date.strftime("%Y-%m-%d")
#
#                         # Increment the count for this date and room type
#                         if date_str not in result[space_subtype_id]:
#                             result[space_subtype_id][date_str] = 1
#                         else:
#                             result[space_subtype_id][date_str] += 1
#
#                         current_date += timedelta(days=1)
#
#             return dict(result)
#         except Exception as e:
#             grLogger.error(f"Error parsing room blocked data: {e}")
#             return {}
#
#     def _parse_availability(self, xml_string_availability):
#         # Parse the XML
#         try:
#             # TODO revisar los caracteres especiales
#             xml_string = xml_string_availability.replace("&", " ")
#             root = ET.fromstring(xml_string)
#
#             result = {}
#
#             # Iterate through the XML structure
#             for revenue in root.findall("hotelRevenues/revenue"):
#                 for th in revenue.findall("th"):
#                     roomTypeID = th.find("roomTypeID").text
#                     date = th.find("day").text
#                     # Convert the date to YYYY-MM-DD format
#                     formatted_date = "-".join(reversed(date.split("/")))
#
#                     # Compute the value as totalRooms - occupancy
#                     totalRooms = int(th.find("totalRooms").text)
#                     occupancy = int(th.find("occupancy").text)
#                     value = totalRooms - occupancy
#
#                     # Update the dictionary
#                     if roomTypeID not in result:
#                         result[roomTypeID] = {}
#                     result[roomTypeID][formatted_date] = value
#
#             result["total"] = result.pop("0")
#             return result
#         except Exception as e:
#             grLogger.error(f"Error {e.args}")
#
#     def _parse_production(self, xml_string: str) -> Dict[str, float]:
#         root = ET.fromstring(xml_string)
#         results = {}
#
#         for production in root.findall(".//production"):
#             day = production.find("day").text
#             total = sum(
#                 float(cc.find("value").text)
#                 for cc in production.findall("cc")
#                 if cc.find("cc_name").text == "Alojamiento"
#             )
#             results[day] = round(total, 2)
#
#         return results
#
#     def _organize_price_data(self, prices):
#         room_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
#
#         for price in prices:
#             price_info = {
#                 "price": str(price.final_price),
#                 "occupancy": str(price.qty_pax),
#             }
#
#             room_data[price.d_date_id][price.space_subtype_id][
#                 price.pms_rate_id
#             ].append(price_info)
#
#         return room_data
#
#     def _create_price_schema(self, room_data):
#         _all = []
#         for date, rooms in room_data.items():
#             for room_type, rates in rooms.items():
#                 for rate_id, prices in rates.items():
#                     room_entry = {
#                         "roomType": str(room_type),
#                         "date": get_ddate_text(ddate_id=date),
#                         "rates": {
#                             "rate": [{"rate_id": str(rate_id), "prices": prices}]
#                         },
#                     }
#                     _all.append(room_entry)
#
#         return {"setAvailability": {"dayAvailibityRoomType": _all}}
#
#     def _send_prices_to_pms(self, property, data):
#
#         _instance = self.bApi.init_call(domain=property.base_url)
#         auth_params = {
#             "auth": {
#                 "pms_id": property.pms_token,
#                 "hotel": property.pms_hotel_identifier,
#                 "usuario": property.pms_username,
#                 "password": property.pms_password,
#             }
#         }
#         data.update(auth_params)
#
#         result = _instance._post(url="/recieve_setavailability_json.php", json=data)
#         return self._handle_pms_response(property.id, result)
#
#     def _handle_pms_response(self, property_id, result):
#         if isinstance(result, dict) and result.get("success") == 1:
#             # Aquí podrías llamar a otro método para manejar las notificaciones de éxito
#             # NotificationHelper.create_notification(event_id=1, property_id=property_id, session=self.session)
#             return True
#         elif isinstance(result, str) and '{"success":1}' in result:
#             # Manejo exitoso, similar al caso anterior
#             # NotificationHelper.create_notification(event_id=1, property_id=property_id, session=self.session)
#             return True
#         else:
#             # Aquí podrías llamar a otro método para manejar las notificaciones de errores
#             # NotificationHelper.create_notification(
#             event_id=1,
#             property_id=property_id,
#             status=2,
#             message="Bad FNS. Fallo en actualizar los precios",
#             session=self.session
#             )
#             return False
