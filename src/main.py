#!/usr/bin/env python3
"""
AutoJobFinder - Async ND/NoDriver Entrypoint
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
import nodriver as uc
import asyncio
from playwright.async_api import async_playwright, Playwright
from autoapply.platforms.linkedin import LinkedInPlatform
from autoapply.platforms.indeed import IndeedPlatform
from autoapply.platforms.glassdoor import GlassdoorPlatform

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def setup_logging(config):
    log_config = config["logging"]
    log_path = PROJECT_ROOT / log_config["file_path"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level=log_config["level"],
        rotation=f"{log_config['max_file_size']} MB",
        retention=log_config["backup_count"],
    )


def save_jobs_csv(jobs, prefix):
    if not jobs:
        return None
    df = pd.DataFrame(jobs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"jobs_{prefix}_{timestamp}.csv"
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(jobs)} jobs to {path}")
    return path


async def run_platform(platform_class, config, tab, name):
    logger.info(f"Starting job search on {name}")
    platform = platform_class(tab, config)
    await platform.login()
    platform_cfg = config["platforms"][name]
    logger.info(
        f"Searching for jobs on {name} with query: {platform_cfg.get('query', '')} and location: {platform_cfg.get('location', '')}"
    )
    jobs = await platform.search_jobs(
        platform_cfg.get("query", ""), platform_cfg.get("location", "")
    )
    logger.info(f"Completed job search on {name}, found {len(jobs)} jobs")
    save_jobs_csv(jobs, name)
    if config["application"].get("apply_active", False):
        count = await platform.apply_to_jobs(jobs)
        logger.info(f"Applied to {count} jobs on {name}")
    return jobs


async def main():
    # Load env and configuration
    load_dotenv(dotenv_path=ENV_PATH)
    config = load_config()
    setup_logging(config)
    browser = await uc.start(
        headless=config["browser"]["headless"],
        browser_executable_path=config["browser"].get("executable_path") or None,
        browser_args=[],  # Add extra chrome args if needed
        # "stealth" param not needed; nodriver handles stealth automatically in latest versions
        # For slow motion, nodriver may not support this param natively—add waits in code if necessary
    )
    # tab = await browser()
    try:
        jobs = {}
        if config["platforms"]["linkedin"]["enabled"]:
            linkedin_tab = await browser.get("https://www.linkedin.com", new_tab=True)
            jobs["linkedin"] = await run_platform(
                LinkedInPlatform, config, linkedin_tab, "linkedin"
            )
        if config["platforms"]["glassdoor"]["enabled"]:
            glassdoor_tab = await browser.new_tab()
            jobs["glassdoor"] = await run_platform(
                GlassdoorPlatform, config, glassdoor_tab, "glassdoor"
            )
        if config["platforms"]["indeed"]["enabled"]:
            platform = IndeedPlatform(browser, config)
            # Assuming IndeedPlatform is NOT browser-based; update if not.
            jobs["indeed"] = await platform.search_jobs()  # If async, use await
            save_jobs_csv(jobs["indeed"], "indeed")
    finally:
        browser.stop()
        # browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
