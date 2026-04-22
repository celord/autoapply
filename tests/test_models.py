"""
Tests for Pydantic job models.
"""

import pytest
from datetime import datetime
from autoapply.models import JobPosting, LinkedInJob, IndeedJob, JobSearchResults
from autoapply.utils.job_converter import convert_jobs_by_platform
from pydantic import ValidationError


class TestJobPosting:
    """Test JobPosting model."""

    def test_valid_job_posting(self):
        """Test creating a valid job posting."""
        job = JobPosting(
            company_name="Tech Corp",
            job_title="Python Developer",
            job_type="Full-time",
            description="Seeking a Python developer...",
            platform="linkedin",
        )

        assert job.company_name == "Tech Corp"
        assert job.job_title == "Python Developer"
        assert job.job_type == "Full-time"
        assert job.platform == "linkedin"

    def test_job_posting_with_datetime(self):
        """Test job posting with datetime."""
        posted = datetime.now()
        job = JobPosting(
            company_name="Acme",
            job_title="Engineer",
            description="Job desc",
            platform="indeed",
            posted_date=posted,
        )

        assert job.posted_date == posted

    def test_job_posting_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            JobPosting(
                company_name="",  # Empty string - invalid
                job_title="Title",
                description="Desc",
                platform="linkedin",
            )

    def test_job_posting_json_serialization(self):
        """Test JSON serialization."""
        job = JobPosting(
            company_name="Tech Corp",
            job_title="Python Developer",
            job_type="Full-time",
            description="Job description",
            platform="linkedin",
            link="https://example.com/job",
        )

        json_str = job.model_dump_json()
        assert "Tech Corp" in json_str
        assert "Python Developer" in json_str


class TestLinkedInJob:
    """Test LinkedInJob model and conversion."""

    def test_linkedin_job_conversion(self):
        """Test converting LinkedIn job to JobPosting."""
        linkedin_job = LinkedInJob(
            title="Senior Python Developer",
            company="Tech Corp",
            link="https://linkedin.com/jobs/123",
            content="We are looking for...",
        )

        job_posting = linkedin_job.to_job_posting()

        assert job_posting.company_name == "Tech Corp"
        assert job_posting.job_title == "Senior Python Developer"
        assert job_posting.platform == "linkedin"
        assert job_posting.link == "https://linkedin.com/jobs/123"


class TestIndeedJob:
    """Test IndeedJob model and conversion."""

    def test_indeed_job_conversion(self):
        """Test converting Indeed job to JobPosting."""
        posted = "2026-04-08T10:00:00"
        indeed_job = IndeedJob(
            title="Backend Engineer",
            company="Data Corp",
            location="Remote",
            description="Backend position",
            link="https://indeed.com/jobs/456",
            job_type="Full-time",
            posted_date=posted,
        )

        job_posting = indeed_job.to_job_posting()

        assert job_posting.company_name == "Data Corp"
        assert job_posting.job_title == "Backend Engineer"
        assert job_posting.job_type == "Full-time"
        assert job_posting.platform == "indeed"
        assert job_posting.posted_date is not None


class TestJobConverter:
    """Test job converter utilities."""

    def test_convert_linkedin_jobs(self):
        """Test converting multiple LinkedIn jobs."""
        raw_jobs = [
            {
                "title": "Python Dev",
                "company": "Corp A",
                "link": "https://...",
                "content": "Description",
            },
            {
                "title": "Java Dev",
                "company": "Corp B",
                "link": "https://...",
                "content": "Description",
            },
        ]

        jobs = convert_jobs_by_platform("linkedin", raw_jobs)

        assert len(jobs) == 2
        assert jobs[0].company_name == "Corp A"
        assert jobs[1].company_name == "Corp B"

    def test_convert_indeed_jobs(self):
        """Test converting Indeed jobs."""
        raw_jobs = [
            {
                "title": "Backend Dev",
                "company": "Tech Inc",
                "location": "Remote",
                "description": "Desc",
                "link": "https://...",
                "job_type": "Full-time",
                "posted_date": "2026-04-08T10:00:00",
            }
        ]

        jobs = convert_jobs_by_platform("indeed", raw_jobs)

        assert len(jobs) == 1
        assert jobs[0].job_type == "Full-time"

    def test_convert_invalid_platform(self):
        """Test converting with invalid platform."""
        jobs = convert_jobs_by_platform("unknown_platform", [])

        assert jobs == []


class TestJobSearchResults:
    """Test JobSearchResults aggregation."""

    def test_add_results(self):
        """Test adding results from multiple platforms."""
        results = JobSearchResults()

        linkedin_jobs = [
            JobPosting(
                company_name="Corp A",
                job_title="Dev",
                description="Desc",
                platform="linkedin",
            )
        ]

        indeed_jobs = [
            JobPosting(
                company_name="Corp B",
                job_title="Engineer",
                description="Desc",
                platform="indeed",
            ),
            JobPosting(
                company_name="Corp C",
                job_title="Dev",
                description="Desc",
                platform="indeed",
            ),
        ]

        results.add_result("linkedin", linkedin_jobs)
        results.add_result("indeed", indeed_jobs)

        assert results.total_jobs == 3
        assert len(results.results) == 2

    def test_get_all_jobs(self):
        """Test retrieving all jobs."""
        results = JobSearchResults()

        jobs1 = [
            JobPosting(
                company_name="A", job_title="Job1", description="D", platform="linkedin"
            )
        ]

        jobs2 = [
            JobPosting(
                company_name="B", job_title="Job2", description="D", platform="indeed"
            )
        ]

        results.add_result("linkedin", jobs1)
        results.add_result("indeed", jobs2)

        all_jobs = results.get_all_jobs()

        assert len(all_jobs) == 2
        assert all_jobs[0].company_name == "A"
        assert all_jobs[1].company_name == "B"
