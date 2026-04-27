from autoapply.platforms.base import BasePlatform
from typing import List, Dict, Any
from loguru import logger
import asyncio
from dotenv import load_dotenv


import os
from urllib.parse import urljoin

TIMEOUT = 4000
JOB_CARD_SELECTOR = "li[data-occludable-job-id]"
RAW_LIST_ITEM_SELECTOR = "li"
JOB_CARD_FALLBACK_SELECTOR = ".job-card-container"
RESULTS_CONTAINER_SELECTORS = (
    ".jobs-search-results-list",
    ".jobs-search-results-list__list",
    ".scaffold-layout__list",
)


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
        await self.page.wait_for_selector(JOB_CARD_SELECTOR)
        await self._load_more_job_cards()

        counts = await self._collect_result_counts()
        raw_li_count = counts[RAW_LIST_ITEM_SELECTOR]
        li_count = counts[JOB_CARD_SELECTOR]
        logger.info(
            "LinkedIn selector counts: "
            f"job_cards={li_count}, "
            f"fallback_cards={counts[JOB_CARD_FALLBACK_SELECTOR]}, "
            f"raw_li={raw_li_count}"
        )
        if li_count == 0:
            logger.error("No LinkedIn job cards found in the primary result list")
            return []
        # max_jobs = min(2, li_count)
        results = []
        # Left side job list
        # card_count = min(
        #     await self.page.locator(f"xpath={CARD_XPATH}").count(), max_jobs
        # )

        async def extract_card_info(card):

            job_title_in_left_card = await safe_text(
                card.locator(
                    'xpath=.//a[contains(@class,"job-card-container__link")]//strong'
                )
            )
            job_title_url_link = await safe_attr(
                card.locator('xpath=.//a[contains(@class,"job-card-container__link")]'),
                "href",
            )
            company_name_left_card = await safe_text(
                card.locator(
                    'xpath=.//div[contains(@class,"artdeco-entity-lockup__subtitle")]//span[1]'
                )
            )
            job_location_left_card = await safe_text(
                card.locator(
                    'xpath=.//ul[contains(@class,"job-card-container__metadata-wrapper")]//li[1]//span[1]'
                )
            )
            easy_apply_left_card = False
            easy_apply_matches = await card.locator(
                'xpath=.//ul[contains(@class,"job-card-container__metadata-wrapper")]//li//span[contains(normalize-space(),"Easy Apply")]'
            ).count()
            if easy_apply_matches > 0:
                easy_apply_left_card = True
            return [
                job_title_in_left_card,
                job_title_url_link,
                company_name_left_card,
                job_location_left_card,
                easy_apply_left_card,
            ]

        for idx in range(li_count):
            logger.info(f"Processing li #{idx + 1} of {li_count}")
            try:
                card = self.page.locator(JOB_CARD_SELECTOR).nth(idx)
                cards = await extract_card_info(card)
                logger.info(f"Cards: {cards}")
                title, raw_link, company, location_text, easy_apply = cards

                if not any([title, raw_link, company, location_text]):
                    logger.info(
                        f"Skipping placeholder card at position {idx + 1}: no extractable fields"
                    )
                    continue

                normalized_link = urljoin("https://www.linkedin.com", raw_link or "")
                results.append(
                    {
                        "title": title or "Unknown title",
                        "company": company or "Unknown company",
                        "location": location_text,
                        "link": normalized_link or None,
                        "url": normalized_link or None,
                        "easy_apply": easy_apply,
                        "content": "",
                    }
                )
                # CARD PANEL FIELDS
            #         job_id = await card.get_attribute("data-occludable-job-id")
            #
            #
            #         # CLICK INTO DETAIL PANEL
            #         await card.click(timeout=TIMEOUT)
            #         detail = self.page.locator(
            #             'xpath=//div[contains(@class,"jobs-search__job-details--wrapper")]'
            #         ).last
            #         await detail.wait_for(state="visible", timeout=TIMEOUT)
            #         await self.page.wait_for_timeout(500)
            #
            #         # DETAIL PANEL FIELDS
            #         detailTitle = await safe_text(
            #             detail.locator('xpath=.//h1[contains(@class,"t-24")] | .//h1')
            #         )
            #         detailCompany = await safe_text(
            #             detail.locator(
            #                 'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__company-name")]//a | .//a[contains(@href,"/company/")]'
            #             )
            #         )
            #         detailCompanyUrl = await safe_attr(
            #             detail.locator(
            #                 'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__company-name")]//a | .//a[contains(@href,"/company/")]'
            #             ),
            #             "href",
            #         )
            #         detailLocation = await safe_text(
            #             detail.locator(
            #                 'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__tertiary-description-container")]//span[contains(@class,"tvm__text--low-emphasis")][1]'
            #             )
            #         )
            #         postedDate = await safe_text(
            #             detail.locator(
            #                 'xpath=.//span[contains(@class,"tvm__text--positive")]'
            #             )
            #         )
            #         engagementItems = await safe_all(
            #             detail.locator(
            #                 'xpath=.//div[contains(@class,"job-details-jobs-unified-top-card__tertiary-description-container")]//span[contains(@class,"tvm__text--low-emphasis")]'
            #             )
            #         )
            #         engagementClean = list({t for t in engagementItems if t != "·"})
            #
            #         tagButtons = await detail.locator(
            #             'xpath=.//div[contains(@class,"job-details-fit-level-preferences")]//button'
            #         ).all()
            #         tags = []
            #         for btn in tagButtons:
            #             strong = btn.locator("xpath=.//strong")
            #             text = await safe_text(strong) or await safe_text(btn)
            #             if text:
            #                 tags.append(text.split("\n")[0].strip())
            #         salary = next((t for t in tags if "$" in t), None)
            #         workType = [
            #             t for t in tags if t and ("$" not in t and "level" not in t.lower())
            #         ]
            #
            #         descriptionText = await safe_text(
            #             detail.locator(
            #                 'xpath=.//div[contains(@class,"jobs-description__content")]'
            #             )
            #         )
            #         try:
            #             descriptionHtml = await detail.locator(
            #                 'xpath=.//div[contains(@class,"jobs-box__html-content")]'
            #             ).first.inner_html(timeout=TIMEOUT)
            #         except Exception:
            #             descriptionHtml = None
            #
            #         isEasyApply = None
            #         try:
            #             btn = detail.locator(
            #                 'xpath=.//button[contains(@class,"jobs-apply-button")]'
            #             ).first
            #             label = (await btn.inner_text(timeout=TIMEOUT)).lower() if btn else ""
            #             isEasyApply = "easy apply" in label
            #         except Exception:
            #             isEasyApply = None
            #         externalApplyUrl = await safe_attr(
            #             detail.locator('xpath=.//a[contains(@class,"jobs-apply-button")]'),
            #             "href",
            #         )
            #
            #         # Compose result
            #         results.append(
            #             {
            #                 "jobId": jobId,
            #                 "url": job_title_url_link,
            #                 "title": detailTitle or job_title_in_left_card,
            #                 "company": detailCompany or company_name_left_card,
            #                 "companyUrl": detailCompanyUrl,
            #                 "companyLogo": logoUrl,
            #                 "location": detailLocation or job_location_left_card,
            #                 "postedDate": postedDate,
            #                 "salary": salary or cardSalary,
            #                 "workplaceType": workType,
            #                 "allTags": tags,
            #                 "engagement": engagementClean,
            #                 "isEasyApply": isEasyApply,
            #                 "externalApplyUrl": externalApplyUrl,
            #                 "cardInsight": cardInsight,
            #                 "cardFooterItems": cardFooterItems,
            #                 "descriptionText": descriptionText,
            #             }
            #         )
            #         logger.info(
            #             f"[{idx + 1}/{card_count}] scraped: {(detailTitle or job_title_in_left_card)}"
            #         )
            except Exception as exc:
                logger.warning(f"Could not process li #{idx + 1}: {exc}")
        # Ensure consistent output and schema matching
        return results

    async def _load_more_job_cards(self, attempts: int = 8) -> None:
        """Scroll the results pane to trigger LinkedIn lazy loading."""
        cards = self.page.locator(JOB_CARD_SELECTOR)
        container = await self._find_results_container()
        previous_count = 0
        plateau_count = 0

        for attempt in range(1, attempts + 1):
            current_count = await cards.count()
            if current_count == 0:
                return

            logger.info(
                f"LinkedIn load attempt {attempt}/{attempts}: rendered {current_count} job cards"
            )

            if current_count == previous_count:
                plateau_count += 1
                if plateau_count >= 2:
                    break
            else:
                plateau_count = 0

            if container is not None:
                await container.evaluate(
                    "element => { element.scrollTop = element.scrollHeight; }"
                )
            else:
                await cards.nth(current_count - 1).evaluate(
                    """
                    element => {
                        const scrollParent = (() => {
                            let node = element.parentElement;
                            while (node) {
                                const style = window.getComputedStyle(node);
                                const overflowY = style.overflowY;
                                if (
                                    (overflowY === 'auto' || overflowY === 'scroll') &&
                                    node.scrollHeight > node.clientHeight
                                ) {
                                    return node;
                                }
                                node = node.parentElement;
                            }
                            return null;
                        })();

                        if (scrollParent) {
                            scrollParent.scrollTop = scrollParent.scrollHeight;
                        } else {
                            element.scrollIntoView({ block: 'end' });
                        }
                    }
                    """
                )
            await self.page.mouse.wheel(0, 1800)
            await self.page.wait_for_timeout(1200)
            previous_count = current_count

    async def _collect_result_counts(self) -> dict[str, int]:
        """Collect count snapshots for the main candidate selectors."""
        selectors = [
            JOB_CARD_SELECTOR,
            JOB_CARD_FALLBACK_SELECTOR,
            RAW_LIST_ITEM_SELECTOR,
        ]
        counts = {}

        for selector in selectors:
            counts[selector] = await self.page.locator(selector).count()

        return counts

    async def _find_results_container(self):
        """Return the first visible results container that can be scrolled."""
        for selector in RESULTS_CONTAINER_SELECTORS:
            container = self.page.locator(selector).first
            try:
                if await container.count() == 0:
                    continue
                return container
            except Exception:
                continue

        return None

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
