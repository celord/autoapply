#!/usr/bin/env python3
"""
AutoJobFinder - Automated Job Search and Application Tool
Author: AutoJobFinder Team
License: MIT
"""

import os
import sys
from collections.abc import Sequence
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import yaml
from loguru import logger
from playwright.async_api import async_playwright
from playwright._impl._api_structures import SetCookieParam
import asyncio
from autoapply.utils.config_loader import ConfigLoader
from autoapply.utils.logger import setup_logger
from autoapply.platforms.linkedin import LinkedInPlatform
from autoapply.platforms.indeed import IndeedPlatform
from autoapply.platforms.glassdoor import GlassdoorPlatform
import time


project_root = Path(__file__).parent.parent


class AutoJobFinder:
    def __init__(self):
        """Initialize AutoJobFinder with configuration and logging."""
        self.config = self._load_config()
        self.setup_logging()
        self.driver = None
        self.platforms = {}

    def _load_config(self):
        """Load configuration from YAML and environment variables."""
        config_path = project_root / "config" / "config.yaml"
        env_path = project_root / ".env"

        # Load environment variables
        load_dotenv(env_path)

        # Load YAML config
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        """Configure logging settings."""
        log_config = self.config["logging"]
        log_path = project_root / log_config["file_path"]
        log_path.parent.mkdir(parents=True, exist_ok=True)

        setup_logger(
            log_path,
            level=log_config["level"],
            rotation=f"{log_config['max_file_size']} MB",
            retention=log_config["backup_count"],
        )


async def main():
    """Main function to run the job search with Playwright."""
    try:
        load_dotenv()
        os.makedirs("logs", exist_ok=True)
        logger.add(
            "logs/job_search_{time}.log",
            rotation="1 day",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        )
        config_path = os.path.join("config", "config.yaml")
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

        li_at = os.getenv("li_at")
        if not li_at:
            logger.error("li_at cookie not found in .env. Exiting.")
            sys.exit(1)

        cookie = SetCookieParam(
            name="li_at",
            value=li_at,
            domain=".linkedin.com",
            path="/",
        )

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=config["browser"]["headless"])
            context = await browser.new_context()
            # Inject LinkedIn li_at cookie
            await context.add_cookies([cookie])
            page = await context.new_page()

            linkedin = LinkedInPlatform(page, config)
            logger.info("LinkedIn platform (playwright) initialized")
            try:
                await linkedin.login()
                logger.info("Successfully logged in to LinkedIn (via cookie)")
            except Exception as e:
                logger.error(f"Failed Playwright login: {e}")
                await browser.close()
                sys.exit(1)

            # Search for jobs
            try:
                jobs = await linkedin.search_jobs(
                    config["platforms"]["linkedin"]["query"],
                    config["platforms"]["linkedin"]["location"],
                )
                logger.info(f"Found {len(jobs)} jobs on LinkedIn")
                if jobs:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_path = f"jobs_linkedin_{timestamp}.csv"
                    try:
                        import pandas as pd

                        df = pd.DataFrame(jobs)
                        df.to_csv(csv_path, index=False)
                        logger.info(f"Saved {len(jobs)} jobs to {csv_path}")
                    except Exception as e:
                        logger.error(f"Error saving jobs to CSV: {e}")
                    for job in jobs:
                        logger.info("---")
                        #dict comprehention to print all the key, values from each job
                        logger.info({k: v for k, v in job.items()})

                    if config["application"]["apply_active"]:
                        try:
                            await linkedin.apply_to_jobs(jobs)
                        except Exception as e:
                            logger.error(f"Error during job application: {e}")
            except Exception as e:
                logger.error(f"Error during job search: {e}")
                raise
            await browser.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
