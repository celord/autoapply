"""
Example demonstrating how to use Pydantic models for job postings.
"""

from autoapply.models import JobPosting, JobSearchResults
from autoapply.utils.job_converter import convert_jobs_by_platform
from datetime import datetime
from loguru import logger


def example_raw_linkedin_jobs():
    """Example of raw LinkedIn job data."""
    return [
        {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "link": "https://linkedin.com/jobs/123",
            "content": "We are looking for a senior Python developer with 5+ years experience...",
        },
        {
            "title": "Full Stack Engineer",
            "company": "StartUp Inc",
            "link": "https://linkedin.com/jobs/456",
            "content": "Join our team as a Full Stack Engineer. Requirements: Python, React, PostgreSQL...",
        },
    ]


def example_raw_indeed_jobs():
    """Example of raw Indeed job data."""
    return [
        {
            "title": "Python Developer",
            "company": "Data Solutions LLC",
            "location": "Remote",
            "description": "Seeking Python developer for data processing role...",
            "link": "https://indeed.com/jobs/789",
            "job_type": "Full-time",
            "posted_date": "2026-04-08T10:00:00",
        },
        {
            "title": "Backend Engineer",
            "company": "Cloud Systems",
            "location": "San Francisco, CA",
            "description": "Backend engineer needed for microservices architecture...",
            "link": "https://indeed.com/jobs/101",
            "job_type": "Full-time",
            "posted_date": "2026-04-07T14:30:00",
        },
    ]


def example_linkedin_to_pydantic():
    """Example: Convert LinkedIn jobs to Pydantic models."""
    logger.info("=== LinkedIn Jobs Example ===")

    raw_jobs = example_raw_linkedin_jobs()
    validated_jobs = convert_jobs_by_platform("linkedin", raw_jobs)

    logger.info(f"Converted {len(validated_jobs)} LinkedIn jobs to Pydantic models\n")

    for job in validated_jobs:
        logger.info(f"Company: {job.company_name}")
        logger.info(f"Title: {job.job_title}")
        logger.info(f"Platform: {job.platform}")
        logger.info(f"Link: {job.link}")
        logger.info(f"Description (first 100 chars): {job.description[:100]}...")
        logger.info("---")

    return validated_jobs


def example_indeed_to_pydantic():
    """Example: Convert Indeed jobs to Pydantic models."""
    logger.info("=== Indeed Jobs Example ===")

    raw_jobs = example_raw_indeed_jobs()
    validated_jobs = convert_jobs_by_platform("indeed", raw_jobs)

    logger.info(f"Converted {len(validated_jobs)} Indeed jobs to Pydantic models\n")

    for job in validated_jobs:
        logger.info(f"Company: {job.company_name}")
        logger.info(f"Title: {job.job_title}")
        logger.info(f"Type: {job.job_type}")
        logger.info(f"Posted: {job.posted_date}")
        logger.info(f"Platform: {job.platform}")
        logger.info(f"Link: {job.link}")
        logger.info("---")

    return validated_jobs


def example_aggregate_results():
    """Example: Aggregate jobs from multiple platforms."""
    logger.info("=== Aggregating Results Example ===")

    linkedin_jobs = convert_jobs_by_platform("linkedin", example_raw_linkedin_jobs())
    indeed_jobs = convert_jobs_by_platform("indeed", example_raw_indeed_jobs())

    # Create aggregated results
    results = JobSearchResults()
    results.add_result("linkedin", linkedin_jobs)
    results.add_result("indeed", indeed_jobs)

    logger.info(f"Total jobs found: {results.total_jobs}")
    logger.info(f"Platforms: {list(results.results.keys())}")

    all_jobs = results.get_all_jobs()
    logger.info(f"\nAll jobs ({len(all_jobs)}):")
    for job in all_jobs:
        logger.info(f"  - {job.job_title} @ {job.company_name} ({job.platform})")

    # Export as JSON
    logger.info("\nExporting to JSON...")
    json_str = results.model_dump_json(indent=2)
    logger.info(f"JSON length: {len(json_str)} characters")

    return results


def example_filter_jobs():
    """Example: Filter jobs by criteria."""
    logger.info("=== Filtering Jobs Example ===")

    results = example_aggregate_results()
    all_jobs = results.get_all_jobs()

    # Filter: Full-time jobs only
    fulltime_jobs = [j for j in all_jobs if j.job_type == "Full-time"]
    logger.info(f"Full-time jobs: {len(fulltime_jobs)}")

    # Filter: LinkedIn jobs only
    linkedin_jobs = [j for j in all_jobs if j.platform == "linkedin"]
    logger.info(f"LinkedIn jobs: {len(linkedin_jobs)}")

    # Filter: Jobs with specific keyword
    python_jobs = [j for j in all_jobs if "python" in j.job_title.lower()]
    logger.info(f"Python-related jobs: {len(python_jobs)}")


if __name__ == "__main__":
    # Setup logging (optional)
    import sys

    logger.remove()  # Remove default handler
    logger.add(sys.stdout, level="INFO", format="{message}")

    # Run examples
    print("\n")
    example_linkedin_to_pydantic()
    print("\n")
    example_indeed_to_pydantic()
    print("\n")
    example_aggregate_results()
    print("\n")
    example_filter_jobs()
