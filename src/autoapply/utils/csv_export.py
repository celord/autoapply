"""
CSV export utilities for job postings.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from loguru import logger
from autoapply.models import JobPosting, JobSearchResults


def jobs_to_csv(
    jobs: List[JobPosting],
    output_path: Optional[str] = None,
    filename_prefix: str = "jobs",
) -> str:
    """
    Export a list of JobPosting models to CSV.

    Args:
        jobs: List of JobPosting Pydantic models
        output_path: Directory path to save CSV (defaults to current directory)
        filename_prefix: Prefix for the filename (default: "jobs")

    Returns:
        str: Path to the created CSV file

    Raises:
        ValueError: If jobs list is empty
        IOError: If file cannot be written
    """
    if not jobs:
        raise ValueError("Cannot export empty jobs list")

    if output_path:
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path.cwd()

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    platform = jobs[0].platform if jobs else "unknown"
    filename = f"{filename_prefix}_{platform}_{timestamp}.csv"
    filepath = output_dir / filename

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "company_name",
                "job_title",
                "job_type",
                "posted_date",
                "platform",
                "link",
                "description",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write job data
            for job in jobs:
                writer.writerow(
                    {
                        "company_name": job.company_name,
                        "job_title": job.job_title,
                        "job_type": job.job_type or "",
                        "posted_date": job.posted_date.isoformat()
                        if job.posted_date
                        else "",
                        "platform": job.platform,
                        "link": job.link or "",
                        "description": job.description,
                    }
                )

        logger.info(f"Exported {len(jobs)} jobs to {filepath}")
        return str(filepath)

    except IOError as e:
        logger.error(f"Error writing to CSV file {filepath}: {e}")
        raise


def results_to_csv(
    results: JobSearchResults, output_path: Optional[str] = None
) -> dict[str, str]:
    """
    Export JobSearchResults to CSV files (one per platform).

    Args:
        results: JobSearchResults aggregate model
        output_path: Directory path to save CSVs

    Returns:
        dict: Mapping of platform name to CSV filepath
    """
    csv_files = {}

    for platform, result in results.results.items():
        try:
            filepath = jobs_to_csv(
                result.jobs, output_path=output_path, filename_prefix="jobs"
            )
            csv_files[platform] = filepath
        except ValueError:
            logger.warning(f"No jobs to export for platform: {platform}")
        except IOError as e:
            logger.error(f"Failed to export {platform} jobs: {e}")

    return csv_files


def jobs_to_csv_string(jobs: List[JobPosting]) -> str:
    """
    Convert jobs to CSV string (not written to file).

    Args:
        jobs: List of JobPosting models

    Returns:
        str: CSV formatted string
    """
    if not jobs:
        return ""

    csv_lines = []

    # Header
    csv_lines.append(
        "company_name,job_title,job_type,posted_date,platform,link,description"
    )

    # Data rows - properly escape CSV fields
    for job in jobs:
        row = [
            _escape_csv_field(job.company_name),
            _escape_csv_field(job.job_title),
            _escape_csv_field(job.job_type or ""),
            job.posted_date.isoformat() if job.posted_date else "",
            job.platform,
            _escape_csv_field(job.link or ""),
            _escape_csv_field(job.description),
        ]
        csv_lines.append(",".join(row))

    return "\n".join(csv_lines)


def _escape_csv_field(field: str) -> str:
    """
    Escape a field for CSV output.

    Args:
        field: Field value to escape

    Returns:
        str: Properly escaped CSV field
    """
    # Wrap in quotes if contains comma, quote, or newline
    if "," in field or '"' in field or "\n" in field:
        # Escape quotes by doubling them
        field = field.replace('"', '""')
        return f'"{field}"'
    return field
