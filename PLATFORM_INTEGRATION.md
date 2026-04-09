# Platform Scraper Integration - Pydantic Models

## Overview

The platform scrapers (LinkedIn, Indeed, Glassdoor) have been integrated with Pydantic models for standardized job data structures and proper CSV export.

## Changes Made

### 1. Base Platform Class (`src/autoapply/platforms/base.py`)

**Updated return types:**
- `search_jobs()` now returns `List[JobPosting]` instead of `List[Dict[str, Any]]`
- `apply_to_jobs()` now accepts `List[JobPosting]` instead of `List[Dict[str, Any]]`

```python
@abstractmethod
async def search_jobs(self, query: str, location: str, **kwargs) -> List[JobPosting]:
    """Returns validated JobPosting Pydantic models."""
    pass
```

### 2. LinkedIn Platform (`src/autoapply/platforms/linkedin.py`)

**Integration flow:**
1. Scrapes raw job data from LinkedIn (title, company, link, description)
2. Collects raw data into dictionaries
3. Converts to Pydantic models using `convert_linkedin_jobs()`
4. Returns `List[JobPosting]`

```python
# Extract raw jobs
raw_results.append({
    "title": title,
    "company": company,
    "link": link,
    "content": description
})

# Convert to Pydantic models
validated_jobs = convert_linkedin_jobs(raw_results)
return validated_jobs
```

**Benefits:**
- Type safety: All jobs guaranteed to have required fields
- Validation: Field values validated at conversion time
- Consistency: Standardized fields across all platforms

### 3. CSV Export Utility (`src/autoapply/utils/csv_export.py`)

New utility module for exporting Pydantic jobs to CSV:

**Main functions:**
- `jobs_to_csv()`: Export list of JobPosting to CSV file
- `results_to_csv()`: Export JobSearchResults (multi-platform) to CSV files
- `jobs_to_csv_string()`: Get CSV content as string
- `_escape_csv_field()`: Properly escape CSV fields

**Features:**
- Automatic timestamp in filename
- Proper CSV escaping for special characters
- Handles multi-line descriptions
- UTF-8 encoding
- ISO 8601 datetime formatting

**Usage:**
```python
from autoapply.utils.csv_export import jobs_to_csv

# Save to CSV
csv_path = jobs_to_csv(
    jobs=validated_jobs,
    output_path="exports",
    filename_prefix="jobs"
)
# Returns: "exports/jobs_linkedin_20260408_143022.csv"
```

### 4. Main Entry Points

**`src/autoapply/main.py`** (Playwright-based)
- Imports `jobs_to_csv` utility
- Calls `search_jobs()` expecting `List[JobPosting]`
- Logs job fields using Pydantic model attributes
- Exports to CSV using new utility

```python
jobs = await linkedin.search_jobs(query, location)  # Returns List[JobPosting]
csv_path = jobs_to_csv(jobs, filename_prefix="jobs")

for job in jobs:
    logger.info(f"Title: {job.job_title}")
    logger.info(f"Company: {job.company_name}")
    logger.info(f"Posted: {job.posted_date}")
```

**`src/main.py`** (Legacy nodriver-based)
- Updated `save_jobs_csv()` to use new utility
- Removed pandas dependency for CSV export
- Handles platform-agnostic job conversion

## Data Flow

```
Raw Scrape Data (Dict)
         ↓
convert_jobs_by_platform()
         ↓
JobPosting (Pydantic Model)
         ↓
jobs_to_csv()
         ↓
CSV File (Properly Formatted)
```

## File Structure

```
src/autoapply/
├── platforms/
│   ├── base.py                  # Updated return types
│   └── linkedin.py              # Integrated with Pydantic
├── utils/
│   ├── csv_export.py            # NEW: CSV export utilities
│   ├── job_converter.py         # Convert raw → Pydantic
│   └── config_loader.py
└── models.py                    # Pydantic definitions

src/
└── main.py                      # Updated save_jobs_csv()

tests/
├── test_models.py               # Model tests
└── test_csv_export.py           # CSV export tests
```

## CSV Output Format

**Columns:**
- `company_name`: Company name (required)
- `job_title`: Job title (required)
- `job_type`: Employment type (Full-time, Part-time, etc.)
- `posted_date`: ISO 8601 datetime string
- `platform`: Source platform (linkedin, indeed, glassdoor)
- `link`: URL to job posting
- `description`: Full job description

**Example row:**
```csv
Tech Corp,Senior Python Developer,Full-time,2026-04-08T10:30:00,linkedin,https://linkedin.com/jobs/123,"We are looking for a senior Python developer with 5+ years experience..."
```

## Type Safety Benefits

**Before (raw dict):**
```python
job = raw_job_dict
title = job.get("title", "N/A")  # String or default
company = job.get("company", "N/A")  # Type unknown
```

**After (Pydantic):**
```python
job: JobPosting = validated_job
title: str = job.job_title  # Guaranteed string
company: str = job.company_name  # Type-safe, validated
```

## Backward Compatibility

⚠️ **Breaking Change**: Platform scrapers now return `List[JobPosting]` instead of `List[Dict]`

**Migration path:**
1. Code expecting dictionaries must be updated
2. Use Pydantic model attributes instead of `.get()` calls
3. CSV export now handled by dedicated utility (not pandas DataFrame)

## Testing

**Test coverage:**
- `tests/test_models.py`: Pydantic model validation
- `tests/test_csv_export.py`: CSV export with edge cases
  - Special character escaping
  - Multiline descriptions
  - UTC datetime formatting
  - Empty fields handling

**Run tests:**
```bash
uv sync --extras test
uv run -- pytest tests/ -v
```

## Next Steps (Optional)

1. Integrate Indeed and Glassdoor scrapers (same pattern)
2. Add database models extending Pydantic
3. Add filtering API for job search results
4. Implement job deduplication across platforms
5. Add JSON export alongside CSV
