"""
Abstract base class for query sources
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class QuerySource(ABC):
    """Abstract base class for query sources"""

    def __init__(self, config):
        """
        Initialize query source

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def fetch_queries(self, count: int) -> list[str]:
        """
        Fetch queries from this source

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the name of this source for logging

        Returns:
            Source name
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this source is currently available

        Returns:
            True if available, False otherwise
        """
        pass

    def get_priority(self) -> int:
        """
        Return priority (lower value = higher priority)

        Default priority is 100. Subclasses can override this method
        to provide custom priority values.

        Returns:
            Priority value
        """
        return 100
