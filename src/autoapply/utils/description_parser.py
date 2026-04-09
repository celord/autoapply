"""
Utility functions for parsing and cleaning job descriptions from raw HTML/text content.
"""

import re
from typing import Optional
from loguru import logger


def clean_description(raw_content: str) -> str:
    """
    Clean raw job description content by removing noise and normalizing whitespace.

    Args:
        raw_content: Raw text/HTML content from job posting

    Returns:
        Cleaned description string
    """
    if not raw_content or not isinstance(raw_content, str):
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", raw_content.strip())

    # Remove common navigation/UI elements
    noise_patterns = [
        r"Show less.*?Show more",
        r"Save job",
        r"Easy Apply",
        r"Report job",
        r"About the job",
        r"About this role",
        r"Job details",
        r"Seniority level.*?(?=\n|$)",
        r"Employment type.*?(?=\n|$)",
        r"Job function.*?(?=\n|$)",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Clean up remaining whitespace
    text = re.sub(r"\s+", " ", text.strip())

    return text


def extract_description_from_linkedin(content: str) -> str:
    """
    Extract job description from LinkedIn job details page content.

    LinkedIn job detail pages typically have:
    - Header with job title, company, location
    - "About the job" section (the actual description)
    - "Show more/Show less" button
    - Apply button and metadata

    Args:
        content: Full page text content from LinkedIn job details

    Returns:
        Cleaned job description
    """
    if not content:
        return ""

    # Look for common LinkedIn description markers
    # Try to find content between common section headers
    description_markers = [
        r"About the job(.*?)(?:About the company|Show less|Show more|Save job|Report job)",
        r"About this role(.*?)(?:About the company|Show less|Show more|Save job|Report job)",
        r"The role(.*?)(?:About the company|Show less|Show more|Save job|Report job)",
        r"Job description(.*?)(?:About the company|Show less|Show more|Save job|Report job)",
    ]

    for marker in description_markers:
        match = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if match:
            description = match.group(1).strip()
            if len(description) > 20:  # Ensure we got actual content
                return clean_description(description)

    # Fallback: if no markers found, take the longest contiguous block of text
    # (likely to be the description if no markers exist)
    paragraphs = [
        p.strip() for p in content.split("\n") if p.strip() and len(p.strip()) > 20
    ]

    if paragraphs:
        # Return the longest paragraph(s) as description
        description = "\n".join(paragraphs[:5])  # Take first 5 substantial paragraphs
        return clean_description(description)

    return clean_description(content)


def extract_description_from_indeed(content: str) -> str:
    """
    Extract job description from Indeed job details page content.

    Indeed job pages typically have:
    - Job title and company info
    - Job details (type, salary, etc.)
    - Full job description text
    - Company info section

    Args:
        content: Full page text content from Indeed job details

    Returns:
        Cleaned job description
    """
    if not content:
        return ""

    # Look for description section markers
    description_markers = [
        r"Job details(.*?)(?:Company details|Frequently asked|Full job description)",
        r"Full job description(.*?)(?:Company details|Qualifications|Requirements)",
        r"Description(.*?)(?:Company details|Apply now|Job type)",
    ]

    for marker in description_markers:
        match = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if match:
            description = match.group(1).strip()
            if len(description) > 20:
                return clean_description(description)

    # Fallback to cleaning full content
    return clean_description(content)


def extract_description_from_glassdoor(content: str) -> str:
    """
    Extract job description from Glassdoor job details page content.

    Glassdoor job pages typically have:
    - Job title and company info
    - Job description (main content)
    - Company info and reviews
    - Similar jobs

    Args:
        content: Full page text content from Glassdoor job details

    Returns:
        Cleaned job description
    """
    if not content:
        return ""

    # Look for description section markers
    description_markers = [
        r"Job Description(.*?)(?:Company Details|About|Similar|Salaries)",
        r"Description(.*?)(?:Requirements|Qualifications|Benefits)",
        r"Overview(.*?)(?:Company Details|About|Similar)",
    ]

    for marker in description_markers:
        match = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if match:
            description = match.group(1).strip()
            if len(description) > 20:
                return clean_description(description)

    # Fallback
    return clean_description(content)


def extract_description_by_platform(platform: str, content: str) -> str:
    """
    Extract and clean job description based on platform.

    Args:
        platform: Platform name ('linkedin', 'indeed', 'glassdoor')
        content: Raw page content from platform

    Returns:
        Cleaned job description
    """
    platform_lower = platform.lower().strip()

    if platform_lower == "linkedin":
        return extract_description_from_linkedin(content)
    elif platform_lower == "indeed":
        return extract_description_from_indeed(content)
    elif platform_lower == "glassdoor":
        return extract_description_from_glassdoor(content)
    else:
        logger.warning(f"Unknown platform: {platform}. Using generic cleanup.")
        return clean_description(content)
