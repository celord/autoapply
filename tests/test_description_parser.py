"""
Tests for the description parser utility.
"""

import pytest
from autoapply.utils.description_parser import (
    clean_description,
    extract_description_from_linkedin,
    extract_description_from_indeed,
    extract_description_from_glassdoor,
    extract_description_by_platform,
)


class TestCleanDescription:
    """Test the clean_description function."""

    def test_clean_description_with_empty_string(self):
        """Test cleaning an empty string."""
        assert clean_description("") == ""
        assert clean_description(None) == ""

    def test_clean_description_with_extra_whitespace(self):
        """Test that extra whitespace is normalized."""
        raw = "This   is   a   test\n\n\nwith   multiple   spaces"
        result = clean_description(raw)
        assert "   " not in result
        assert result == "This is a test with multiple spaces"

    def test_clean_description_removes_noise(self):
        """Test that common navigation elements are removed."""
        raw = "About the job Software Engineer Save job Easy Apply"
        result = clean_description(raw)
        assert "Save job" not in result
        assert "Easy Apply" not in result

    def test_clean_description_with_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        raw = "   This is a test   "
        result = clean_description(raw)
        assert result == "This is a test"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_clean_description_with_tabs_and_newlines(self):
        """Test that tabs and newlines are normalized."""
        raw = "Line one\t\tLine two\n\nLine three"
        result = clean_description(raw)
        assert "\t" not in result
        assert "\n" not in result


class TestLinkedInDescriptionExtraction:
    """Test LinkedIn-specific description extraction."""

    def test_extract_linkedin_about_the_job_section(self):
        """Test extraction of 'About the job' section."""
        content = """
        Senior Software Engineer
        Acme Corp
        About the job
        We are looking for a senior software engineer with 5+ years of experience.
        This is a full-time position.
        Show more
        Show less
        Save job
        """
        result = extract_description_from_linkedin(content)
        assert "senior software engineer" in result.lower()
        assert "Save job" not in result
        assert "Show" not in result

    def test_extract_linkedin_about_this_role_section(self):
        """Test extraction of 'About this role' section."""
        content = """
        Product Manager
        TechCo
        About this role
        Lead product strategy for our flagship platform.
        Manage cross-functional teams.
        Apply Now
        """
        result = extract_description_from_linkedin(content)
        assert "product strategy" in result.lower()

    def test_extract_linkedin_no_markers(self):
        """Test extraction when no section markers are present."""
        content = """
        Senior Engineer position requiring Python, Go, and Rust skills.
        5+ years of experience in backend systems.
        Experience with distributed systems is a plus.
        """
        result = extract_description_from_linkedin(content)
        assert len(result) > 0
        assert "Senior Engineer" in result or "senior" in result.lower()

    def test_extract_linkedin_empty_content(self):
        """Test extraction with empty content."""
        result = extract_description_from_linkedin("")
        assert result == ""

    def test_extract_linkedin_short_content(self):
        """Test extraction with very short content."""
        result = extract_description_from_linkedin("Too short")
        # Should fallback to clean_description
        assert result == "Too short"


class TestIndeedDescriptionExtraction:
    """Test Indeed-specific description extraction."""

    def test_extract_indeed_job_details_section(self):
        """Test extraction of 'Job details' section."""
        content = """
        Python Developer
        Company XYZ
        Job details
        We need a Python developer for our backend team.
        Must have 3+ years of experience.
        Company details
        We are a startup founded in 2020.
        """
        result = extract_description_from_indeed(content)
        assert "Python developer" in result or "python" in result.lower()
        assert "Company details" not in result

    def test_extract_indeed_full_job_description(self):
        """Test extraction of 'Full job description' section."""
        content = """
        Software Engineer
        TechCorp
        Full job description
        Develop and maintain microservices.
        Write unit and integration tests.
        Company details
        We have 500+ employees.
        """
        result = extract_indeed_job_description(content)
        assert "microservices" in result.lower()

    def test_extract_indeed_empty_content(self):
        """Test extraction with empty content."""
        result = extract_description_from_indeed("")
        assert result == ""


class TestGlassdoorDescriptionExtraction:
    """Test Glassdoor-specific description extraction."""

    def test_extract_glassdoor_job_description_section(self):
        """Test extraction of 'Job Description' section."""
        content = """
        Senior Manager
        Company ABC
        Job Description
        Manage a team of 10+ engineers.
        Drive product strategy and roadmap.
        Company Details
        Founded in 2015, 1000+ employees.
        Similar Jobs
        """
        result = extract_description_from_glassdoor(content)
        assert "engineer" in result.lower()
        assert "Company Details" not in result

    def test_extract_glassdoor_description_section(self):
        """Test extraction of generic 'Description' section."""
        content = """
        QA Engineer
        QA Company
        Description
        Test automation and manual testing.
        Collaborate with developers.
        Requirements
        5+ years of QA experience.
        """
        result = extract_description_from_glassdoor(content)
        assert "test" in result.lower()
        assert "Requirements" not in result

    def test_extract_glassdoor_empty_content(self):
        """Test extraction with empty content."""
        result = extract_description_from_glassdoor("")
        assert result == ""


class TestPlatformAgnosticExtraction:
    """Test platform-agnostic extraction."""

    def test_extract_by_platform_linkedin(self):
        """Test extraction with 'linkedin' platform."""
        content = "About the job We are hiring. Save job"
        result = extract_description_by_platform("linkedin", content)
        assert "We are hiring" in result
        assert "Save job" not in result

    def test_extract_by_platform_indeed(self):
        """Test extraction with 'indeed' platform."""
        content = "Job details Apply here. Company details"
        result = extract_description_by_platform("indeed", content)
        assert "Apply here" in result

    def test_extract_by_platform_glassdoor(self):
        """Test extraction with 'glassdoor' platform."""
        content = "Job Description Great company. Similar Jobs"
        result = extract_description_by_platform("glassdoor", content)
        assert "Great company" in result

    def test_extract_by_platform_case_insensitive(self):
        """Test that platform name is case-insensitive."""
        content = "About the job Test description. Save job"
        result1 = extract_description_by_platform("LinkedIn", content)
        result2 = extract_description_by_platform("LINKEDIN", content)
        result3 = extract_description_by_platform("linkedin", content)
        assert result1 == result2 == result3

    def test_extract_by_platform_unknown(self):
        """Test extraction with unknown platform."""
        content = "Some description with extra  spaces."
        result = extract_description_by_platform("unknown", content)
        assert "Some description" in result
        assert "  " not in result

    def test_extract_by_platform_empty_content(self):
        """Test extraction with empty content."""
        result = extract_description_by_platform("linkedin", "")
        assert result == ""


class TestRealWorldScenarios:
    """Test with realistic job description scenarios."""

    def test_linkedin_job_with_html_entities(self):
        """Test LinkedIn job with HTML-like content."""
        content = """
        About the job
        We&rsquo;re looking for a senior engineer &mdash; someone who&rsquo;s passionate about building great products.
        Responsibilities:
        • Design and build scalable systems
        • Mentor junior engineers
        Save job
        """
        result = extract_description_from_linkedin(content)
        assert len(result) > 0
        assert "engineer" in result.lower()

    def test_description_with_bullet_points(self):
        """Test description parsing with bullet points."""
        content = """
        About the job
        Key Responsibilities:
        • Lead technical architecture decisions
        • Mentor team members
        • Drive innovation
        Required Skills:
        • 5+ years experience
        • Python expertise
        About the company
        """
        result = extract_description_from_linkedin(content)
        assert "Lead" in result or "lead" in result.lower()
        assert "About the company" not in result

    def test_description_with_multiline_sections(self):
        """Test description with multiple lines and sections."""
        content = """
        About the job
        This is a unique opportunity to join our team.
        
        We're looking for:
        - Experienced developers
        - Team players
        - People who love learning
        
        What we offer:
        - Competitive salary
        - Remote work
        - Professional development
        
        Save job
        """
        result = extract_description_from_linkedin(content)
        assert "experienced" in result.lower()
        assert "Save job" not in result
        assert len(result) > 50  # Should capture substantial content


# Helper function for testing (if needed)
def extract_indeed_job_description(content: str) -> str:
    """Helper function matching Indeed extraction."""
    return extract_description_from_indeed(content)
