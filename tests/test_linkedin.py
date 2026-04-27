"""
Async test suite for LinkedIn platform (Playwright)
"""

import pytest
from unittest.mock import AsyncMock, Mock
from autoapply.platforms.linkedin import LinkedInPlatform


@pytest.fixture
def mock_page():
    # Use AsyncMock to mock Playwright's async Page
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock()
    page.mouse = Mock()
    page.mouse.wheel = AsyncMock()
    # Set realistic return values for awaited selectors and methods as needed
    page.url = "https://www.linkedin.com/jobs"
    return page


@pytest.fixture
def mock_config():
    return {
        "search": {
            "keywords": "Python Developer",
            "location": "New York",
            "job_type": "F",
            "date_posted": "7",
            "experience_level": "ENTRY_LEVEL",
        },
        "platforms": {"linkedin": {"enabled": True, "search_limit": 10}},
        "application": {"apply_active": False, "resume_path": "resumes/resume.pdf"},
        "delays": {"min_delay": 1, "max_delay": 3, "page_load_timeout": 10},
        "browser": {"headless": True},
    }


@pytest.fixture
def linkedin_platform(mock_page, mock_config):
    return LinkedInPlatform(mock_page, mock_config)


@pytest.mark.asyncio
async def test_linkedin_login_success(linkedin_platform):
    # Set up mock for Playwright selectors
    linkedin_platform.page.query_selector.return_value = AsyncMock()
    await linkedin_platform.login()
    assert linkedin_platform.login_executed


@pytest.mark.asyncio
async def test_search_jobs_uses_job_card_selector(linkedin_platform):
    job_cards = Mock()
    job_cards.count = AsyncMock(return_value=0)

    def locator_side_effect(selector):
        if selector == "li[data-occludable-job-id]":
            return job_cards
        fallback = Mock()
        fallback.count = AsyncMock(return_value=0)
        return fallback

    linkedin_platform.page.locator = Mock(side_effect=locator_side_effect)
    linkedin_platform._load_more_job_cards = AsyncMock()
    linkedin_platform._collect_result_counts = AsyncMock(
        return_value={
            "li[data-occludable-job-id]": 0,
            ".job-card-container": 0,
            "li": 0,
        }
    )

    jobs = await linkedin_platform.search_jobs("python", "remote")

    assert jobs == []
    linkedin_platform.page.wait_for_selector.assert_awaited_once_with(
        "li[data-occludable-job-id]"
    )
    linkedin_platform._load_more_job_cards.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_jobs_returns_extracted_card_data(linkedin_platform):
    card = Mock()

    def card_locator_side_effect(selector):
        locator = Mock()
        locator.first = locator
        locator.count = AsyncMock(return_value=0)

        text_values = {
            'xpath=.//a[contains(@class,"job-card-container__link")]//strong': "Python Developer",
            'xpath=.//div[contains(@class,"artdeco-entity-lockup__subtitle")]//span[1]': "Acme",
            'xpath=.//ul[contains(@class,"job-card-container__metadata-wrapper")]//li[1]//span[1]': "Remote",
        }
        attr_values = {
            'xpath=.//a[contains(@class,"job-card-container__link")]': "/jobs/view/123/",
        }

        locator.inner_text = AsyncMock(return_value=text_values.get(selector))
        locator.get_attribute = AsyncMock(return_value=attr_values.get(selector))
        return locator

    card.locator = Mock(side_effect=card_locator_side_effect)

    cards_locator = Mock()
    cards_locator.count = AsyncMock(return_value=1)
    cards_locator.nth = Mock(return_value=card)

    def page_locator_side_effect(selector):
        if selector == "li[data-occludable-job-id]":
            return cards_locator
        fallback = Mock()
        fallback.count = AsyncMock(return_value=0)
        return fallback

    linkedin_platform.page.locator = Mock(side_effect=page_locator_side_effect)
    linkedin_platform._load_more_job_cards = AsyncMock()
    linkedin_platform._collect_result_counts = AsyncMock(
        return_value={
            "li[data-occludable-job-id]": 1,
            ".job-card-container": 1,
            "li": 3,
        }
    )

    jobs = await linkedin_platform.search_jobs("python", "remote")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[0]["company"] == "Acme"
    assert jobs[0]["location"] == "Remote"
    assert jobs[0]["link"] == "https://www.linkedin.com/jobs/view/123/"


@pytest.mark.asyncio
async def test_load_more_job_cards_scrolls_last_visible_card(linkedin_platform):
    cards = Mock()
    last_card = Mock()
    last_card.evaluate = AsyncMock()
    cards.count = AsyncMock(side_effect=[3, 5, 5, 5])
    cards.nth = Mock(return_value=last_card)
    linkedin_platform.page.locator = Mock(return_value=cards)
    linkedin_platform.page.wait_for_timeout = AsyncMock()
    linkedin_platform._find_results_container = AsyncMock(return_value=None)

    await linkedin_platform._load_more_job_cards()

    assert cards.nth.call_args_list[0].args[0] == 2
    assert cards.nth.call_args_list[1].args[0] == 4
    assert cards.nth.call_args_list[2].args[0] == 4
    assert last_card.evaluate.await_count == 3
    assert linkedin_platform.page.mouse.wheel.await_count == 3


@pytest.mark.asyncio
async def test_load_more_job_cards_scrolls_results_container_when_present(
    linkedin_platform,
):
    cards = Mock()
    cards.count = AsyncMock(side_effect=[3, 5, 5, 5])
    cards.nth = Mock()
    container = Mock()
    container.evaluate = AsyncMock()

    linkedin_platform.page.locator = Mock(return_value=cards)
    linkedin_platform.page.wait_for_timeout = AsyncMock()
    linkedin_platform._find_results_container = AsyncMock(return_value=container)

    await linkedin_platform._load_more_job_cards()

    assert container.evaluate.await_count == 3
    cards.nth.assert_not_called()
    assert linkedin_platform.page.mouse.wheel.await_count == 3
