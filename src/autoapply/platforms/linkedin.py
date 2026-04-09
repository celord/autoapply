from autoapply.platforms.base import BasePlatform
from autoapply.models import JobPosting
from autoapply.utils.job_converter import convert_linkedin_jobs
from typing import List, Dict, Any
from loguru import logger
import asyncio
from dotenv import load_dotenv


import os


class LinkedInPlatform(BasePlatform):
    def __init__(self, page, config: dict):
        super().__init__(page, config)
        self.page = page
        self.login_executed = False
        super().__init__(self.tab, config)
        load_dotenv()
        # Fetch and inject the li_at cookie using Playwright's context.add_cookies at startup
        # user-data-dir that has been logged into LinkedIn manually. See documentation for instructions.
        self.login_executed = False

    async def login(self) -> None:
        """
        Ensure session is authenticated by loading LinkedIn and checking page state.
        The session is now established by Playwright cookie injection (li_at).
        """
        cookie_object = {
            "name": "li_at",
            "value": os.getenv("li_at"),
            "domain": ".linkedin.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
        }

        await self.page.context.add_cookies([cookie_object])
        await self.page.goto("https://www.linkedin.com/feed")
        await asyncio.sleep(2)
        # Quick check: look for presence of user profile or login button
        if await self.page.query_selector(
            "a[data-control-name='identity_welcome_message']"
        ):
            logger.info("LinkedIn session is authenticated (via cookie).")
        elif await self.page.query_selector("input[name='session_key']"):
            logger.error("li_at cookie was not valid: not logged in to LinkedIn.")
        else:
            logger.warning("Login state undetermined. Check the profile manually.")
        self.login_executed = True
        return

    async def search_jobs(
        self, query: str, location: str, **kwargs
    ) -> List[JobPosting]:
        """Search for jobs on LinkedIn and return Pydantic models."""
        # Extract params from config (use defaults if not provided)
        cfg = self.config.get("platforms", {}).get("linkedin", {})
        query = cfg.get("query", "python")
        geo_id = cfg.get("geo_id", "")
        date_posted = cfg.get("date_posted", "")  # "1" for past 24 hours
        work_type = cfg.get("work_type", "")

        url = f"https://www.linkedin.com/jobs/search/?keywords={query}"
        if geo_id:
            url += f"&geoId={geo_id}"
        if date_posted:
            url += f"&f_TPR=r86400" if date_posted == "1" else f"&f_TPR={date_posted}"
        if work_type:
            url += f"&f_WT={work_type}"

        await self.page.goto(url)
        await self.page.wait_for_timeout(4000)
        # Find the main job cards list (no iframe in 2026)
        # Wait for the true job results list based on latest xpath
        await self.page.wait_for_selector(
            "main div > div:nth-child(2) > div:nth-child(1) > div > ul > li"
        )
        list_locator = self.page.locator(
            "main div > div:nth-child(2) > div:nth-child(1) > div > ul"
        )
        li_count = await list_locator.locator("li").count()
        if li_count == 0:
            logger.error("No <li> elements found in the primary result list!")
            return []
        max_jobs = min(2, li_count)
        raw_results = []
        for idx in range(max_jobs):
            li = list_locator.locator("li").nth(idx)
            try:
                await li.scroll_into_view_if_needed()
                # Robust title extraction
                title, link, company = None, None, None
                # Try typical selectors
                card = None
                if await li.locator(".base-card").count() > 0:
                    card = li.locator(".base-card")
                elif await li.locator(".job-search-card").count() > 0:
                    card = li.locator(".job-search-card")
                else:
                    card = li  # fallback: operate on li itself
                # Title
                for selector in [
                    ".base-search-card__title",
                    ".job-search-card__title",
                    "h3",
                    "a",
                    "span",
                ]:
                    if await card.locator(selector).count() > 0:
                        title = await card.locator(selector).first.inner_text()
                        logger.info(
                            f"- Using selector '{selector}' for title: {title.strip()}"
                        )
                        break
                # Link
                for selector in [
                    "a.base-card__full-link",
                    "a.job-search-card__link",
                    "a",
                ]:
                    if await card.locator(selector).count() > 0:
                        link = await card.locator(selector).first.get_attribute("href")
                        logger.info(f"- Using selector '{selector}' for link: {link}")
                        break
                # Company
                for selector in [
                    ".base-search-card__subtitle a",
                    ".job-search-card__company-name",
                    "h4 > a",
                    "h4",
                    "span",
                ]:
                    if await card.locator(selector).count() > 0:
                        company = await card.locator(selector).first.inner_text()
                        logger.info(
                            f"- Using selector '{selector}' for company: {company.strip()}"
                        )
                        break
                logger.info(f"Job li {idx + 1}: {title} @ {company} ({link})")
                await li.click()
                await self.page.wait_for_timeout(2000)
                await self.page.wait_for_selector(
                    ".jobs-details__main-content, .jobs-description__container"
                )
                detail_area = None
                for sel in [
                    ".jobs-details__main-content",
                    ".jobs-description__container",
                ]:
                    elems = await self.page.query_selector_all(sel)
                    if elems:
                        detail_area = elems[0]
                        break
                if detail_area:
                    main = await detail_area.inner_text()
                    logger.info(f"Job {idx + 1} MAIN CONTENT:\n{main[:800]}\n---")
                    raw_results.append(
                        {
                            "title": (title or "").strip(),
                            "company": (company or "").strip(),
                            "link": link,
                            "content": main,
                        }
                    )
                else:
                    logger.warning(f"No detail area found for job #{idx + 1}.")
            except Exception as exc:
                logger.warning(f"Could not process li #{idx + 1}: {exc}")

        # Convert raw results to Pydantic models
        validated_jobs = convert_linkedin_jobs(raw_results)
        logger.info(
            f"Converted {len(raw_results)} raw jobs to {len(validated_jobs)} validated JobPosting models"
        )
        return validated_jobs

    async def apply_to_jobs(self, jobs: List[JobPosting]) -> int:
        """
        Async: Apply to jobs on LinkedIn, handling Easy Apply where possible.

        Args:
            jobs: List of JobPosting Pydantic models

        Returns:
            int: Number of successful job applications
        """
        if not self.config["application"].get("apply_active", False):
            logger.info("Auto-apply is disabled in configuration")
            return 0
        logger.info(f"Processing {len(jobs)} LinkedIn jobs")
        applications = 0
        for job in jobs:
            if job.get("applied"):
                continue
            try:
                logger.info(
                    f"Opening application for: {job['title']} at {job['company']}"
                )
                await self.page.goto(job["link"])
                await self.random_delay(3, 5)
                apply_button = await self.page.query_selector(
                    "button[data-control-name='jobdetails_topcard_inapply']"
                )
                if apply_button:
                    label_raw = await apply_button.inner_text()
                    label = label_raw.lower() if label_raw else ""
                    if "easy apply" in label:
                        await self.safe_click(apply_button)
                        result = await self._submit_easy_apply()
                        if result:
                            job["applied"] = True
                            logger.info(f"Successfully applied to job: {job['title']}")
                            applications += 1
                        else:
                            logger.info(
                                f"Could not complete application: {job['title']}"
                            )
                    else:
                        logger.info(f"Button not Easy Apply: {label}")
                        job["applied"] = False
                else:
                    logger.info(f"No Easy Apply button found: {job['link']}")
                    job["applied"] = False
                await self.random_delay()
            except Exception as e:
                logger.error(f"Error processing LinkedIn job: {e}")
                continue
        return applications

    async def _submit_easy_apply(self) -> bool:
        """
        Async: Handle Easy Apply application submission loop.
        Returns True if successful, False otherwise.
        """
        try:
            while True:
                await self._handle_application_questions()
                # Try next or submit buttons
                next_btn = await self.page.query_selector(
                    "button[aria-label='Continue to next step']"
                )
                if next_btn:
                    await self.safe_click(next_btn)
                    await self.random_delay()
                    continue
                submit_btn = await self.page.query_selector(
                    "button[aria-label='Submit application']"
                )
                if submit_btn:
                    await self.safe_click(submit_btn)
                    await self.random_delay()
                    return True
                # If neither, consider application finished (or interrupted)
                break
        except Exception as e:
            logger.error(f"Error during Easy Apply submission: {e}")
            return False
        return False

    async def _handle_application_questions(self) -> None:
        """
        Async: Fills simple questions with dummy placeholder data (for Easy Apply flows).
        """
        try:
            # Find all input fields in the active Easy Apply dialog
            questions = await self.page.query_selector_all(
                "div.jobs-easy-apply-form-section__input input, div.jobs-easy-apply-form-section__input textarea"
            )
            for q in questions:
                try:
                    qtype = await q.get_attribute("type")
                    if qtype == "text":
                        await q.fill("Yes")
                    elif qtype == "radio" or qtype == "checkbox":
                        if hasattr(q, "is_checked") and callable(
                            getattr(q, "is_checked", None)
                        ):
                            is_checked = await q.is_checked()
                        else:
                            is_checked = False
                        if not is_checked:
                            await self.safe_click(q)
                except Exception as e:
                    logger.warning(f"Error handling application question: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error finding application questions: {e}")
