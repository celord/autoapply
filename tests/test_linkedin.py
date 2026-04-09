"""
Async test suite for LinkedIn platform (Playwright)
"""

import pytest
from unittest.mock import AsyncMock
from autoapply.platforms.linkedin import LinkedInPlatform


@pytest.fixture
def mock_page():
    # Use AsyncMock to mock Playwright's async Page
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock()
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
