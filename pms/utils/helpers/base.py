from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from properties.models import Property


class BasePropertyHelper(ABC):
    """Abstract base class for all property helpers.

    This class defines a common interface for all property helpers regardless
    of the underlying PMS (Property Management System).
    """

    def __init__(self, prop: Property):
        """Initialize the property helper."""
        self.setup_api_client(prop)

    @abstractmethod
    def setup_api_client(self, prop: Property) -> None:
        """Set up the API client specific to this PMS."""
        ...

    @abstractmethod
    def download_room_list(self, prop: Property) -> dict:
        """Download the room list from the PMS."""
        ...

    @abstractmethod
    def download_property_details(self, prop: Property) -> dict:
        """Download property details from the PMS."""
        ...

    @abstractmethod
    def download_reservations(
        self, prop: Property, checkin: Optional[date] = None
    ) -> List[dict]:
        """Download reservations from the PMS."""
        ...

    @abstractmethod
    def download_rates_and_availability(
        self,
        prop: Property,
        checkin: Optional[date] = None,
        checkout: Optional[date] = None,
    ) -> List[dict]:
        """Download rates and availability from the PMS."""
        ...

    @abstractmethod
    def download_availability(self, prop: Property) -> List[dict]:
        """Download availability from the PMS."""
        ...
