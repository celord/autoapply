"""
Indeed platform implementation
"""

import os
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urlencode

from .base import BasePlatform


class IndeedPlatform(BasePlatform):
    """Indeed job search platform implementation."""

    def __init__(self, driver, config):
        """Initialize Indeed platform."""
        super().__init__(driver, config)
        self.base_url = "https://www.indeed.com"
        self.api_key = os.getenv("INDEED_API_KEY")

    def login(self) -> None:
        """
        Indeed doesn't require login for basic job search.
        API key is used for advanced features.
        """
        if not self.api_key:
            logger.warning("Indeed API key not found. Some features may be limited.")
        logger.info("Indeed platform initialized")

    async def search_jobs(self) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed using BeautifulSoup for parsing.

        Returns:
            List[Dict[str, Any]]: List of job listings
        """
        try:
            logger.info("Starting Indeed job search")
            jobs = []
            search_limit = self.config["platforms"]["indeed"]["search_limit"]

            # Build search URL
            params = {
                "q": self.config["search"]["keywords"],
                "l": self.config["search"]["location"],
                "jt": self.config["search"]["job_type"],
                "fromage": self.config["search"]["date_posted"],
                "limit": search_limit,
            }
            search_url = f"{self.base_url}/jobs?{urlencode(params)}"

            # Make request with anti-detection headers
            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.indeed.com",
                "DNT": "1",
            }

            response = requests.get(search_url, headers=headers)
            response.raise_for_status()

            # Parse job listings
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="job_seen_beacon")

            for card in job_cards[:search_limit]:
                try:
                    job_data = self._extract_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error extracting job data: {e}")
                    continue

                await self.random_delay()  # Anti-detection delay

            logger.info(f"Found {len(jobs)} jobs on Indeed")
            return jobs

        except Exception as e:
            logger.error(f"Error during Indeed job search: {e}")
            raise

    def _extract_job_data(self, card) -> Dict[str, Any]:
        """
        Extract job data from a BeautifulSoup job card element.

        Args:
            card: BeautifulSoup element representing a job card

        Returns:
            Dict[str, Any]: Job data dictionary
        """
        try:
            # Extract job title and link
            title_elem = card.find("h2", class_="jobTitle")
            title = title_elem.get_text(strip=True)
            job_link = self.base_url + title_elem.find("a")["href"]

            # Extract company name
            company_elem = card.find("span", class_="companyName")
            company = (
                company_elem.get_text(strip=True)
                if company_elem
                else "Company not listed"
            )

            # Extract location
            location_elem = card.find("div", class_="companyLocation")
            location = (
                location_elem.get_text(strip=True)
                if location_elem
                else "Location not specified"
            )

            # Extract job description
            description_elem = card.find("div", class_="job-snippet")
            description = (
                description_elem.get_text(strip=True)
                if description_elem
                else "Description not available"
            )

            return {
                "platform": "Indeed",
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "url": job_link,
                "applied": False,
            }

        except Exception as e:
            logger.warning(f"Error extracting job data from card: {e}")
            return None

    async def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Apply to jobs on Indeed.
        Note: Indeed's application process varies by employer and often redirects to company websites.
        This implementation focuses on tracking rather than automated application.

        Args:
            jobs (List[Dict[str, Any]]): List of jobs to track applications for
        """
        if not self.config["application"]["apply_active"]:
            logger.info("Auto-apply is disabled in configuration")
            return

        logger.info(f"Processing {len(jobs)} Indeed jobs")

        for job in jobs:
            if job.get("applied"):
                continue

            try:
                logger.info(
                    f"Opening application for: {job['title']} at {job['company']}"
                )
                self.driver.get(job["url"])

                # Note: We don't implement actual application automation for Indeed
                # as it typically redirects to external sites
                logger.info(f"Job requires manual application: {job['url']}")
                job["applied"] = False  # Mark as requiring manual application

                await self.random_delay()

            except Exception as e:
                logger.error(f"Error processing Indeed job: {e}")
                continue

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        from fake_useragent import UserAgent

        return UserAgent().random
