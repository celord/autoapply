"""
Pydantic models for job postings and related data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobPosting(BaseModel):
    """
    Represents a job posting from any platform.

    Attributes:
        company_name: Name of the company posting the job
        job_title: Title/position of the job
        job_type: Type of employment (e.g., 'Full-time', 'Part-time', 'Contract')
        description: Full job description text
        posted_date: Date and time when the job was posted (ISO format or None if not available)
        link: URL to the job posting
        platform: Source platform ('linkedin', 'indeed', 'glassdoor')
    """

    company_name: str = Field(..., min_length=1, description="Name of the company")
    job_title: str = Field(..., min_length=1, description="Job title/position")
    job_type: Optional[str] = Field(
        None, description="Employment type (e.g., Full-time, Part-time)"
    )
    description: str = Field(..., min_length=1, description="Job description content")
    posted_date: Optional[datetime] = Field(None, description="When the job was posted")
    link: Optional[str] = Field(None, description="URL to the job posting")
    platform: str = Field(
        ..., description="Source platform (linkedin, indeed, glassdoor)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "job_title": "Senior Software Engineer",
                "job_type": "Full-time",
                "description": "We are looking for a senior software engineer...",
                "posted_date": "2026-04-08T10:30:00",
                "link": "https://linkedin.com/jobs/12345",
                "platform": "linkedin",
            }
        }


class LinkedInJob(BaseModel):
    """LinkedIn-specific job model (internal parsing)."""

    title: str
    company: str
    link: Optional[str] = None
    content: str

    def to_job_posting(self) -> JobPosting:
        """Convert LinkedIn job to standardized JobPosting."""
        return JobPosting(
            company_name=self.company,
            job_title=self.title,
            job_type=None,  # LinkedIn doesn't provide this in the parsed content
            description=self.content,
            posted_date=None,  # Would need additional parsing
            link=self.link,
            platform="linkedin",
        )


class IndeedJob(BaseModel):
    """Indeed-specific job model (internal parsing)."""

    title: str
    company: str
    location: Optional[str] = None
    description: str
    link: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None

    def to_job_posting(self) -> JobPosting:
        """Convert Indeed job to standardized JobPosting."""
        # Try to parse posted_date if it's in a known format
        parsed_date = None
        if self.posted_date:
            try:
                # Handle various date formats if needed
                parsed_date = datetime.fromisoformat(self.posted_date)
            except (ValueError, TypeError):
                parsed_date = None

        return JobPosting(
            company_name=self.company,
            job_title=self.title,
            job_type=self.job_type,
            description=self.description,
            posted_date=parsed_date,
            link=self.link,
            platform="indeed",
        )


class GlassdoorJob(BaseModel):
    """Glassdoor-specific job model (internal parsing)."""

    title: str
    company: str
    location: Optional[str] = None
    description: str
    link: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    salary_range: Optional[str] = None

    def to_job_posting(self) -> JobPosting:
        """Convert Glassdoor job to standardized JobPosting."""
        parsed_date = None
        if self.posted_date:
            try:
                parsed_date = datetime.fromisoformat(self.posted_date)
            except (ValueError, TypeError):
                parsed_date = None

        return JobPosting(
            company_name=self.company,
            job_title=self.title,
            job_type=self.job_type,
            description=self.description,
            posted_date=parsed_date,
            link=self.link,
            platform="glassdoor",
        )


class JobSearchResult(BaseModel):
    """Result of a job search across platforms."""

    platform: str
    jobs_found: int
    jobs: list[JobPosting]
    timestamp: datetime = Field(default_factory=datetime.now)


class JobSearchResults(BaseModel):
    """Aggregated results from searching multiple platforms."""

    results: dict[str, JobSearchResult] = Field(default_factory=dict)
    total_jobs: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)

    def add_result(self, platform: str, jobs: list[JobPosting]) -> None:
        """Add jobs from a platform to the results."""
        self.results[platform] = JobSearchResult(
            platform=platform, jobs_found=len(jobs), jobs=jobs
        )
        self.total_jobs += len(jobs)

    def get_all_jobs(self) -> list[JobPosting]:
        """Get all jobs across all platforms."""
        all_jobs = []
        for result in self.results.values():
            all_jobs.extend(result.jobs)
        return all_jobs
