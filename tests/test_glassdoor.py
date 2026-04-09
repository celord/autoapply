"""
Async test suite for Glassdoor platform (nodriver)
"""

import pytest
from unittest.mock import AsyncMock, patch
from autoapply.platforms.glassdoor import GlassdoorPlatform


@pytest.fixture
def mock_config():
    return {
        "search": {
            "keywords": "Python Developer",
            "location": "New York",
            "job_type": "fulltime",
            "date_posted": "7",
            "experience_level": "entry_level",
        },
        "platforms": {"glassdoor": {"enabled": True, "search_limit": 10}},
        "application": {"apply_active": False},
        "delays": {"min_delay": 1, "max_delay": 3, "page_load_timeout": 10},
    }


@pytest.fixture
def mock_tab():
    tab = AsyncMock()
    tab.url = "https://www.glassdoor.com/jobs"
    return tab


@pytest.fixture
def glassdoor_platform(mock_tab, mock_config):
    return GlassdoorPlatform(mock_tab, mock_config)


@pytest.mark.asyncio
async def test_glassdoor_apply_to_jobs_disabled(glassdoor_platform):
    jobs = [
        {
            "title": "DevOps Engineer",
            "company": "TestCo",
            "url": "https://job",
            "applied": False,
        }
    ]
    n_applied = await glassdoor_platform.apply_to_jobs(jobs)
    assert n_applied == 0


@pytest.mark.asyncio
async def test_glassdoor_apply_to_jobs_enables_and_clicks(glassdoor_platform, mock_tab):
    glassdoor_platform.config["application"]["apply_active"] = True
    jobs = [
        {
            "title": "QA Engineer",
            "company": "TestCo",
            "url": "https://job2",
            "applied": False,
        }
    ]

    # Simulate an apply button found
    mock_apply_btn = AsyncMock()
    mock_tab.query_selector.return_value = mock_apply_btn
    glassdoor_platform.tab = mock_tab
    glassdoor_platform.safe_click = AsyncMock()

    n_applied = await glassdoor_platform.apply_to_jobs(jobs)
    assert n_applied == 1
    # Should call goto and query_selector for each job
    mock_tab.goto.assert_awaited_with(jobs[0]["url"])
    mock_tab.query_selector.assert_awaited_with("button[data-test='apply-button']")
    glassdoor_platform.safe_click.assert_awaited_with(mock_apply_btn)
    assert jobs[0]["applied"] is False


@pytest.mark.asyncio
async def test_glassdoor_apply_to_jobs_no_apply_button(glassdoor_platform, mock_tab):
    glassdoor_platform.config["application"]["apply_active"] = True
    jobs = [
        {
            "title": "QA Engineer",
            "company": "TestCo",
            "url": "https://job2",
            "applied": False,
        }
    ]
    # Simulate no button found
    mock_tab.query_selector.return_value = None
    glassdoor_platform.tab = mock_tab
    glassdoor_platform.safe_click = AsyncMock()

    n_applied = await glassdoor_platform.apply_to_jobs(jobs)
    assert n_applied == 1
    mock_tab.goto.assert_awaited_with(jobs[0]["url"])
    mock_tab.query_selector.assert_awaited_with("button[data-test='apply-button']")
    glassdoor_platform.safe_click.assert_not_awaited()
    assert jobs[0]["applied"] is False


@pytest.mark.asyncio
async def test_glassdoor_apply_to_jobs_errors_logged(glassdoor_platform, mock_tab):
    glassdoor_platform.config["application"]["apply_active"] = True
    jobs = [
        {
            "title": "QA Engineer",
            "company": "TestCo",
            "url": "https://job3",
            "applied": False,
        }
    ]
    # Simulate an exception on goto
    mock_tab.goto.side_effect = Exception("Network error")
    glassdoor_platform.tab = mock_tab
    glassdoor_platform.safe_click = AsyncMock()

    n_applied = await glassdoor_platform.apply_to_jobs(jobs)
    assert n_applied == 0
    mock_tab.goto.assert_awaited_with(jobs[0]["url"])
    # Should log error and job remains not applied
    assert jobs[0]["applied"] is False
