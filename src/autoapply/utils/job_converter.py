"""
Utility functions for converting platform-specific job data to Pydantic models.
"""

from typing import List, Dict, Any
from loguru import logger
from autoapply.models import JobPosting, LinkedInJob, IndeedJob, GlassdoorJob


def convert_linkedin_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobPosting]:
    """
    Convert raw LinkedIn job dictionaries to JobPosting models.

    Args:
        raw_jobs: List of raw job dictionaries from LinkedIn scraper

    Returns:
        List of validated JobPosting models
    """
    validated_jobs = []
    for raw_job in raw_jobs:
        try:
            linkedin_job = LinkedInJob(
                title=raw_job.get("title", ""),
                company=raw_job.get("company", ""),
                link=raw_job.get("link"),
                content=raw_job.get("content", ""),
            )
            validated_jobs.append(linkedin_job.to_job_posting())
        except Exception as e:
            logger.warning(f"Failed to validate LinkedIn job: {e}")
            continue

    return validated_jobs


def convert_indeed_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobPosting]:
    """
    Convert raw Indeed job dictionaries to JobPosting models.

    Args:
        raw_jobs: List of raw job dictionaries from Indeed scraper

    Returns:
        List of validated JobPosting models
    """
    validated_jobs = []
    for raw_job in raw_jobs:
        try:
            indeed_job = IndeedJob(
                title=raw_job.get("title", ""),
                company=raw_job.get("company", ""),
                location=raw_job.get("location"),
                description=raw_job.get("description", ""),
                link=raw_job.get("link"),
                job_type=raw_job.get("job_type"),
                posted_date=raw_job.get("posted_date"),
            )
            validated_jobs.append(indeed_job.to_job_posting())
        except Exception as e:
            logger.warning(f"Failed to validate Indeed job: {e}")
            continue

    return validated_jobs


def convert_glassdoor_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobPosting]:
    """
    Convert raw Glassdoor job dictionaries to JobPosting models.

    Args:
        raw_jobs: List of raw job dictionaries from Glassdoor scraper

    Returns:
        List of validated JobPosting models
    """
    validated_jobs = []
    for raw_job in raw_jobs:
        try:
            glassdoor_job = GlassdoorJob(
                title=raw_job.get("title", ""),
                company=raw_job.get("company", ""),
                location=raw_job.get("location"),
                description=raw_job.get("description", ""),
                link=raw_job.get("link"),
                job_type=raw_job.get("job_type"),
                posted_date=raw_job.get("posted_date"),
                salary_range=raw_job.get("salary_range"),
            )
            validated_jobs.append(glassdoor_job.to_job_posting())
        except Exception as e:
            logger.warning(f"Failed to validate Glassdoor job: {e}")
            continue

    return validated_jobs


def convert_jobs_by_platform(
    platform: str, raw_jobs: List[Dict[str, Any]]
) -> List[JobPosting]:
    """
    Convert raw job dictionaries from any platform to JobPosting models.

    Args:
        platform: Platform name ('linkedin', 'indeed', 'glassdoor')
        raw_jobs: List of raw job dictionaries

    Returns:
        List of validated JobPosting models
    """
    platform_lower = platform.lower().strip()

    if platform_lower == "linkedin":
        return convert_linkedin_jobs(raw_jobs)
    elif platform_lower == "indeed":
        return convert_indeed_jobs(raw_jobs)
    elif platform_lower == "glassdoor":
        return convert_glassdoor_jobs(raw_jobs)
    else:
        logger.warning(f"Unknown platform: {platform}. Skipping validation.")
        return []
