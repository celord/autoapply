from autoapply.platforms.base import BasePlatform
from typing import List, Dict, Any
from loguru import logger


class GlassdoorPlatform(BasePlatform):
    async def login(self) -> None:
        """Stub login for tests."""
        return

    async def search_jobs(
        self, query: str, location: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """Stub search_jobs for tests."""
        return []

    async def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Async: Apply to jobs on Glassdoor, tracking application attempts.
        Note: Most jobs redirect off-platform, so we only simulate/track here.
        Returns:
            int: Number of application attempts made
        """
        if not self.config["application"].get("apply_active", False):
            logger.info("Auto-apply is disabled in configuration")
            return 0
        logger.info(f"Processing {len(jobs)} Glassdoor jobs")
        applications = 0
        for job in jobs:
            if job.get("applied"):
                continue
            try:
                logger.info(
                    f"Opening application for: {job['title']} at {job['company']}"
                )
                await self.tab.goto(job["url"])
                # Check for apply button
                apply_button = await self.tab.query_selector(
                    "button[data-test='apply-button']"
                )
                if apply_button:
                    await self.safe_click(apply_button)
                    logger.info(f"Job requires external application: {job['url']}")
                    job["applied"] = False
                else:
                    logger.info(f"No direct apply button found: {job['url']}")
                    job["applied"] = False
                await self.random_delay()
                applications += 1
            except Exception as e:
                logger.error(f"Error processing Glassdoor job: {e}")
                continue
        return applications
