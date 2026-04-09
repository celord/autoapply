"""
Test Indeed platform functionality (async-compatible)
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
from autoapply.platforms.indeed import IndeedPlatform


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
        "platforms": {"indeed": {"enabled": True, "search_limit": 10}},
        "application": {"apply_active": False},
        "delays": {"min_delay": 1, "max_delay": 3, "page_load_timeout": 10},
    }


@pytest.fixture
def indeed_platform(mock_config):
    return IndeedPlatform(None, mock_config)


def test_indeed_initialization(indeed_platform):
    assert indeed_platform.base_url == "https://www.indeed.com"
    assert indeed_platform.config is not None


def test_indeed_login(indeed_platform):
    indeed_platform.login()
    # No exception should be raised


@patch("requests.get")
def test_indeed_search_jobs(mock_get, indeed_platform):
    html_content = """
    <div class="job_seen_beacon">
        <h2 class="jobTitle"><a href="/job/123">Senior Python Developer</a></h2>
        <span class="companyName">Test Company</span>
        <div class="companyLocation">New York, NY</div>
        <div class="job-snippet">Job description here</div>
    </div>
    """
    mock_response = Mock()
    mock_response.text = html_content
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    jobs = asyncio.run(indeed_platform.search_jobs())
    assert len(jobs) > 0
    assert jobs[0]["platform"] == "Indeed"
    assert jobs[0]["title"] == "Senior Python Developer"
    assert jobs[0]["company"] == "Test Company"
    assert jobs[0]["location"] == "New York, NY"
    assert not jobs[0]["applied"]


def test_indeed_extract_job_data(indeed_platform):
    html = """
    <div class="job_seen_beacon">
        <h2 class="jobTitle"><a href="/job/123">Python Developer</a></h2>
        <span class="companyName">ABC Corp</span>
        <div class="companyLocation">Remote</div>
        <div class="job-snippet">Great opportunity!</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    card = soup.find("div", class_="job_seen_beacon")

    job_data = indeed_platform._extract_job_data(card)
    assert job_data is not None
    assert job_data["title"] == "Python Developer"
    assert job_data["company"] == "ABC Corp"
    assert job_data["location"] == "Remote"
    assert job_data["platform"] == "Indeed"
    assert not job_data["applied"]
