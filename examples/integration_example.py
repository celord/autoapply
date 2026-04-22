#!/usr/bin/env python3
"""
Integration example: End-to-end job search with Pydantic models and CSV export.

This demonstrates:
1. Scraping jobs (returns Pydantic JobPosting models)
2. Validating and filtering jobs
3. Exporting to CSV with proper formatting
"""

from autoapply.models import JobPosting, JobSearchResults
from autoapply.utils.job_converter import convert_jobs_by_platform
from autoapply.utils.csv_export import jobs_to_csv, results_to_csv
from datetime import datetime
from loguru import logger
import sys


def example_full_workflow():
    """Demonstrate a complete job search workflow."""

    # Setup logging
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="{message}")

    logger.info("=== Full Integration Example ===\n")

    # 1. Simulate scraped job data from multiple platforms
    logger.info("1. Simulating job scraping from multiple platforms...")

    linkedin_raw = [
        {
            "title": "Senior Python Developer",
            "company": "Tech Corp",
            "link": "https://linkedin.com/jobs/1",
            "content": "We seek a senior Python developer with 5+ years experience in distributed systems...",
        },
        {
            "title": "Full Stack Engineer",
            "company": "StartUp Inc",
            "link": "https://linkedin.com/jobs/2",
            "content": "Join our fast-growing startup. Stack: Python, React, PostgreSQL...",
        },
    ]

    indeed_raw = [
        {
            "title": "Python Developer",
            "company": "Data Solutions",
            "location": "Remote",
            "description": "Seeking Python developer for data pipeline development",
            "link": "https://indeed.com/jobs/1",
            "job_type": "Full-time",
            "posted_date": "2026-04-08T09:00:00",
        },
        {
            "title": "Backend Engineer",
            "company": "Cloud Systems",
            "location": "San Francisco, CA",
            "description": "Backend engineer for microservices architecture",
            "link": "https://indeed.com/jobs/2",
            "job_type": "Full-time",
            "posted_date": "2026-04-07T14:30:00",
        },
    ]

    logger.info(f"  - LinkedIn: {len(linkedin_raw)} raw jobs")
    logger.info(f"  - Indeed: {len(indeed_raw)} raw jobs\n")

    # 2. Convert raw data to Pydantic models
    logger.info("2. Converting raw data to Pydantic JobPosting models...")

    linkedin_jobs = convert_jobs_by_platform("linkedin", linkedin_raw)
    indeed_jobs = convert_jobs_by_platform("indeed", indeed_raw)

    logger.info(f"  - LinkedIn: {len(linkedin_jobs)} validated jobs")
    logger.info(f"  - Indeed: {len(indeed_jobs)} validated jobs\n")

    # 3. Aggregate results
    logger.info("3. Aggregating results from all platforms...")

    results = JobSearchResults()
    results.add_result("linkedin", linkedin_jobs)
    results.add_result("indeed", indeed_jobs)

    logger.info(f"  - Total jobs found: {results.total_jobs}")
    logger.info(f"  - Platforms: {list(results.results.keys())}\n")

    # 4. Display and filter jobs
    logger.info("4. Filtering and displaying jobs...")

    all_jobs = results.get_all_jobs()

    # Filter: Full-time only
    fulltime_jobs = [j for j in all_jobs if j.job_type == "Full-time"]
    logger.info(f"  - Full-time positions: {len(fulltime_jobs)}")

    # Filter: Contains "Python" in title
    python_jobs = [j for j in all_jobs if "python" in j.job_title.lower()]
    logger.info(f"  - Python-related jobs: {len(python_jobs)}\n")

    # 5. Display sample jobs
    logger.info("5. Sample jobs:")
    for i, job in enumerate(all_jobs[:3], 1):
        logger.info(f"\n  Job {i}:")
        logger.info(f"    Company: {job.company_name}")
        logger.info(f"    Title: {job.job_title}")
        logger.info(f"    Type: {job.job_type or 'Not specified'}")
        logger.info(f"    Posted: {job.posted_date or 'Not specified'}")
        logger.info(f"    Platform: {job.platform}")
        logger.info(f"    Link: {job.link or 'N/A'}")
        logger.info(f"    Description (first 80 chars): {job.description[:80]}...")

    # 6. Export to CSV
    logger.info("\n6. Exporting results to CSV...")

    try:
        # Export all jobs together
        csv_path = jobs_to_csv(all_jobs, filename_prefix="jobs_all")
        logger.info(f"  - Exported all jobs: {csv_path}")

        # Export per-platform
        platform_csv_files = results_to_csv(results)
        for platform, filepath in platform_csv_files.items():
            logger.info(f"  - Exported {platform}: {filepath}")
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return

    # 7. Display statistics
    logger.info("\n7. Search Statistics:")
    logger.info(f"  - Total jobs: {results.total_jobs}")
    logger.info(f"  - By platform:")
    for platform, result in results.results.items():
        logger.info(f"    - {platform}: {result.jobs_found} jobs")

    logger.info(f"  - By type:")
    job_types = {}
    for job in all_jobs:
        job_type = job.job_type or "Unknown"
        job_types[job_type] = job_types.get(job_type, 0) + 1
    for job_type, count in job_types.items():
        logger.info(f"    - {job_type}: {count} jobs")

    logger.info(f"\n✓ Workflow completed successfully!")


if __name__ == "__main__":
    example_full_workflow()
