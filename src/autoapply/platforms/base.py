"""
Base platform class for job search platforms using async nodriver.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger
import asyncio
import random


class BasePlatform(ABC):
    """Async base class for job search platform implementations using nodriver."""

    def __init__(self, tab, config: dict):
        """
        Initialize the platform.

        Args:
            tab: nodriver Tab or Page object
            config (dict): Application configuration
        """
        self.tab = tab
        self.config = config

    @abstractmethod
    async def login(self) -> None:
        """Asynchronously log in to the platform (if required)."""
        pass

    @abstractmethod
    async def search_jobs(
        self, query: str, location: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously search for jobs on the platform.

        Args:
            query (str): Job search query/keywords
            location (str): Job location
        Returns:
            List[Dict[str, Any]]: List of job postings info
        """
        pass

    @abstractmethod
    async def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Asynchronously apply to a list of jobs.

        Args:
            jobs (List[Dict[str, Any]]): List of job posting information
        Returns:
            int: Number of successful job applications
        """
        pass

    async def random_delay(self, min_sec=1, max_sec=3):
        """
        Async helper to sleep randomly to emulate human interaction.
        """
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scroll_to_selector(self, selector: str):
        """
        Scroll element into view using nodriver by CSS selector.
        Args:
            selector (str): CSS selector for the element
        """
        # nodriver .eval or .scroll_into_view for element
        element = await self.tab.query_selector(selector)
        if element:
            await element.scroll_into_view()
            await self.random_delay()
