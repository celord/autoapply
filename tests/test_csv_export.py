"""
Tests for CSV export functionality.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from autoapply.models import JobPosting
from autoapply.utils.csv_export import (
    jobs_to_csv,
    jobs_to_csv_string,
    _escape_csv_field,
    results_to_csv,
)
from autoapply.models import JobSearchResults


class TestCSVExport:
    """Test CSV export utilities."""

    @pytest.fixture
    def sample_jobs(self):
        """Create sample jobs for testing."""
        return [
            JobPosting(
                company_name="Tech Corp",
                job_title="Senior Python Developer",
                job_type="Full-time",
                description="We are looking for a senior Python developer...",
                link="https://example.com/job1",
                platform="linkedin",
                posted_date=datetime(2026, 4, 8, 10, 30, 0),
            ),
            JobPosting(
                company_name="Data Inc",
                job_title="Data Engineer",
                job_type="Full-time",
                description="Join our data team...",
                link="https://example.com/job2",
                platform="linkedin",
            ),
        ]

    def test_jobs_to_csv_file(self, sample_jobs):
        """Test exporting jobs to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = jobs_to_csv(
                sample_jobs, output_path=tmpdir, filename_prefix="test"
            )

            # Verify file was created
            assert Path(filepath).exists()
            assert "test_linkedin_" in filepath
            assert filepath.endswith(".csv")

            # Verify content
            with open(filepath, "r") as f:
                lines = f.readlines()

            assert len(lines) == 3  # Header + 2 jobs
            assert "company_name" in lines[0]
            assert "Tech Corp" in lines[1]
            assert "Data Inc" in lines[2]

    def test_jobs_to_csv_empty_list(self):
        """Test that empty jobs list raises error."""
        with pytest.raises(ValueError):
            jobs_to_csv([])

    def test_jobs_to_csv_string(self, sample_jobs):
        """Test converting jobs to CSV string."""
        csv_str = jobs_to_csv_string(sample_jobs)

        assert "company_name" in csv_str
        assert "Tech Corp" in csv_str
        assert "Data Inc" in csv_str
        assert "Senior Python Developer" in csv_str

        lines = csv_str.split("\n")
        assert len(lines) == 3

    def test_jobs_to_csv_string_empty(self):
        """Test CSV string with empty jobs."""
        csv_str = jobs_to_csv_string([])
        assert csv_str == ""

    def test_escape_csv_field_simple(self):
        """Test escaping simple fields."""
        assert _escape_csv_field("Hello") == "Hello"
        assert _escape_csv_field("123") == "123"

    def test_escape_csv_field_with_comma(self):
        """Test escaping fields with commas."""
        result = _escape_csv_field("Smith, John")
        assert result == '"Smith, John"'

    def test_escape_csv_field_with_quote(self):
        """Test escaping fields with quotes."""
        result = _escape_csv_field('He said "hello"')
        assert result == '"He said ""hello"""'

    def test_escape_csv_field_with_newline(self):
        """Test escaping fields with newlines."""
        result = _escape_csv_field("Line1\nLine2")
        assert result == '"Line1\nLine2"'

    def test_csv_content_correct_fields(self, sample_jobs):
        """Test that all fields are exported correctly."""
        csv_str = jobs_to_csv_string(sample_jobs)

        # Check header
        header = csv_str.split("\n")[0]
        fields = header.split(",")
        expected_fields = [
            "company_name",
            "job_title",
            "job_type",
            "posted_date",
            "platform",
            "link",
            "description",
        ]
        assert fields == expected_fields

    def test_csv_datetime_formatting(self, sample_jobs):
        """Test that datetime is formatted as ISO string."""
        csv_str = jobs_to_csv_string(sample_jobs)

        # First job has datetime
        assert "2026-04-08T10:30:00" in csv_str

        # Second job has no datetime (empty field)
        lines = csv_str.split("\n")
        # Count commas - should have 7 fields per line
        assert len(lines[1].split(",")) == 7  # First data row with datetime

    def test_results_to_csv(self, sample_jobs):
        """Test exporting JobSearchResults."""
        results = JobSearchResults()
        results.add_result("linkedin", sample_jobs)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_files = results_to_csv(results, output_path=tmpdir)

            assert "linkedin" in csv_files
            assert Path(csv_files["linkedin"]).exists()

    def test_csv_multiline_description(self):
        """Test CSV export with multiline descriptions."""
        jobs = [
            JobPosting(
                company_name="Corp",
                job_title="Role",
                description="Line 1\nLine 2\nLine 3",
                platform="indeed",
            )
        ]

        csv_str = jobs_to_csv_string(jobs)
        lines = csv_str.split("\n")

        # Description should be escaped with quotes
        assert '"Line 1\nLine 2\nLine 3"' in csv_str

    def test_csv_special_characters(self):
        """Test CSV with special characters."""
        jobs = [
            JobPosting(
                company_name='Corp "Special" Inc',
                job_title="Role with, comma",
                description='Description with\nneeds "escaping"',
                platform="linkedin",
            )
        ]

        csv_str = jobs_to_csv_string(jobs)

        # All special characters should be properly escaped
        assert '""Special""' in csv_str
        assert '"Role with, comma"' in csv_str
        assert '""escaping""' in csv_str
