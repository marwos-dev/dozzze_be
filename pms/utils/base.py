from abc import ABC, abstractmethod
from typing import Dict, Tuple

from properties.models import Property

# from src.utils.func_utils import get_ddate_text, replace_day


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
        pass

    @abstractmethod
    def download_availability(self, prop: Property) -> Dict:
        """Download availability data from the PMS.

        Args:
            prop: Property dictionary containing API credentials
            start_date_id: Start date ID for the availability query
            end_date_id: End date ID for the availability query

        Returns:
            Dictionary containing availability data
        """
        pass

    @abstractmethod
    def download_revenue(self, prop: Property) -> Dict:
        """Download revenue data from the PMS.

        Args:
            prop: Property dictionary containing API credentials
            start_date_id: Start date ID for the revenue query
            end_date_id: End date ID for the revenue query

        Returns:
            Dictionary containing revenue data by date
        """
        pass

    @abstractmethod
    def download_blocked(self, prop: Property) -> Dict:
        """Download blocked rooms data from the PMS.

        Args:
            prop: Property dictionary containing API credentials
            start_date_id: Start date ID for the blocked rooms query
            end_date_id: End date ID for the blocked rooms query

        Returns:
            Dictionary containing blocked rooms data
        """
        pass

    # Common utility methods for all property helpers

    def get_date_range(self, start_date_id: int, end_date_id: int) -> Tuple[str, str]:
        """Convert date IDs to formatted date strings.

        Args:
            start_date_id: Start date ID
            end_date_id: End date ID

        Returns:
            Tuple of formatted date strings (start_date, end_date)
        """
        # start_date = replace_day(get_ddate_text(start_date_id))  # First day of month
        # end_date = get_ddate_text(end_date_id)
        # return start_date, end_date
        return "1", "2"

    def log_error(self, operation: str, error: Exception) -> None:
        """Log error information.

        Args:
            operation: The operation that failed
            error: The exception that was raised
        """
        print(f"Error during {operation}: {str(error)}")
