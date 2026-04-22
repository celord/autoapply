from autoapply.platforms.base import BasePlatform
from typing import List, Dict, Any
from loguru import logger
import asyncio
from dotenv import load_dotenv


import os

TIMEOUT=4000

# --- Helpers for robust field extraction ---
async def safe_text(locator):
    try:
        item = locator.first
        text = await item.inner_text(timeout=TIMEOUT)
        return text.strip()
    except Exception:
        return None


async def safe_attr(locator, attr):
    try:
        item = locator.first
        return await item.get_attribute(attr, timeout=TIMEOUT)
    except Exception:
        return None


async def safe_all(locator):
    try:
        items = await locator.all()
        out = []
        for e in items:
            text = await e.inner_text(timeout=TIMEOUT)
            if text and text.strip():
                out.append(text.strip())
        return out
    except Exception:
        return []


class LinkedInPlatform(BasePlatform):
    def __init__(self, page, config: dict):
        super().__init__(page, config)
        self.page = page
        self.login_executed = False
        load_dotenv()
        # Fetch and inject the li_at cookie using Playwright's context.add_cookies at startup
        # user-data-dir that has been logged into LinkedIn manually. See documentation for instructions.

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
        await self.page.goto("https://www.linkedin.com/")
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
    ) -> List[Dict[str, Any]]:
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
        CARD_XPATH = "//li[@data-occludable-job-id]"
        await self.page.wait_for_selector(f"xpath={CARD_XPATH}", timeout=TIMEOUT)
        li_count = await self.page.locator(f"xpath={CARD_XPATH}").count()
        if li_count == 0:
            logger.error("No <li> elements found in the primary result list!")
            return []
        max_jobs = min(2, li_count)
        results = []
        # Left side job list
        card_count = min(
            await self.page.locator(f"xpath={CARD_XPATH}").count(), max_jobs
        )
        for idx in range(card_count):
            try:
                card = self.page.locator(f"xpath={CARD_XPATH}").nth(idx)
                await card.scroll_into_view_if_needed(timeout=TIMEOUT)
                # CARD PANEL FIELDS
                jobId = await card.get_attribute("data-occludable-job-id")
                cardTitle = await safe_text(
                    card.locator(
                        'xpath=.//a[contains(@class,"job-card-container__link")]//strong'
                    )
                )
                cardUrl = await safe_attr(
                    card.locator(
                        'xpath=.//a[contains(@class,"job-card-container__link")]'
                    ),
                    "href",
                )
                cardCompany = await safe_text(
                    card.locator(
                        'xpath=.//div[contains(@class,"artdeco-entity-lockup__subtitle")]//span[1]'
                    )
                )
                cardLocation = await safe_text(
                    card.locator(
                        'xpath=.//ul[contains(@class,"job-card-container__metadata-wrapper")]//li[1]//span[1]'
                    )
                )
                cardSalary = await safe_text(
                    card.locator(
                        'xpath=.//div[contains(@class,"artdeco-entity-lockup__metadata")]//li[1]//span[1]'
                    )
                )
                cardFooterItems = await safe_all(
                    card.locator(
                        'xpath=.//ul[contains(@class,"job-card-list__footer-wrapper")]//li'
                    )
                )
                logoUrl = await safe_attr(
                    card.locator(
                        'xpath=.//img[contains(@class,"job-card-list__logo")]'
                    ),
                    "src",
                )
                cardInsight = await safe_text(
                    card.locator(
                        'xpath=.//div[contains(@class,"job-card-container__job-insight-text")]'
                    )
                )

                # CLICK INTO DETAIL PANEL
                await card.click(timeout=TIMEOUT)
                detail = self.page.locator(
                    'xpath=//div[contains(@class,"jobs-search__job-details--wrapper")]'
                ).last
                await detail.wait_for(state="visible", timeout=TIMEOUT)
                await self.page.wait_for_timeout(500)

                # DETAIL PANEL FIELDS
                detailTitle = await safe_text(
                    detail.locator('xpath=.//h1[contains(@class,"t-24")] | .//h1')
                )
                detailCompany = await safe_text(
                    detail.locator(
                        'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__company-name")]//a | .//a[contains(@href,"/company/")]'
                    )
                )
                detailCompanyUrl = await safe_attr(
                    detail.locator(
                        'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__company-name")]//a | .//a[contains(@href,"/company/")]'
                    ),
                    "href",
                )
                detailLocation = await safe_text(
                    detail.locator(
                        'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__tertiary-description-container")]//span[contains(@class,"tvm__text--low-emphasis")][1]'
                    )
                )
                postedDate = await safe_text(
                    detail.locator(
                        'xpath=.//span[contains(@class,"tvm__text--positive")]'
                    )
                )
                engagementItems = await safe_all(
                    detail.locator(
                        'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__tertiary-description-container")]//span[contains(@class,"tvm__text--low-emphasis")]'
                    )
                )
                engagementClean = list({t for t in engagementItems if t != "·"})

                tagButtons = await detail.locator(
                    'xpath=.//div[contains(@class,"job-details-fit-level-preferences")]//button'
                ).all()
                tags = []
                for btn in tagButtons:
                    strong = btn.locator("xpath=.//strong")
                    text = await safe_text(strong) or await safe_text(btn)
                    if text:
                        tags.append(text.split("\n")[0].strip())
                salary = next((t for t in tags if "$" in t), None)
                workType = [
                    t for t in tags if t and ("$" not in t and "level" not in t.lower())
                ]

                descriptionText = await safe_text(
                    detail.locator(
                        'xpath=.//div[contains(@class,"jobs-description__content")]'
                    )
                )
                try:
                    descriptionHtml = await detail.locator(
                        'xpath=.//div[contains(@class,"jobs-box__html-content")]'
                    ).first.inner_html(timeout=TIMEOUT)
                except Exception:
                    descriptionHtml = None

                isEasyApply = None
                try:
                    btn = detail.locator(
                        'xpath=.//button[contains(@class,"jobs-apply-button")]'
                    ).first
                    label = (await btn.inner_text(timeout=TIMEOUT)).lower() if btn else ""
                    isEasyApply = "easy apply" in label
                except Exception:
                    isEasyApply = None
                externalApplyUrl = await safe_attr(
                    detail.locator('xpath=.//a[contains(@class,"jobs-apply-button")]'),
                    "href",
                )

                # Compose result
                results.append(
                    {
                        "jobId": jobId,
                        "url": cardUrl,
                        "title": detailTitle or cardTitle,
                        "company": detailCompany or cardCompany,
                        "companyUrl": detailCompanyUrl,
                        "companyLogo": logoUrl,
                        "location": detailLocation or cardLocation,
                        "postedDate": postedDate,
                        "salary": salary or cardSalary,
                        "workplaceType": workType,
                        "allTags": tags,
                        "engagement": engagementClean,
                        "isEasyApply": isEasyApply,
                        "externalApplyUrl": externalApplyUrl,
                        "cardInsight": cardInsight,
                        "cardFooterItems": cardFooterItems,
                        "descriptionText": descriptionText,
                    }
                )
                logger.info(
                    f"[{idx + 1}/{card_count}] scraped: {(detailTitle or cardTitle)}"
                )
            except Exception as exc:
                logger.warning(f"Could not process li #{idx + 1}: {exc}")
        # Ensure consistent output and schema matching
        return results

    async def apply_to_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Async: Apply to jobs on LinkedIn, handling Easy Apply where possible.
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
