# Pydantic Job Models

This module provides Pydantic models for standardized job posting data structures across all supported job platforms (LinkedIn, Indeed, Glassdoor).

## Models

### JobPosting

The main model representing a standardized job posting:

```python
from autoapply.models import JobPosting

job = JobPosting(
    company_name="Acme Corp",
    job_title="Senior Software Engineer",
    job_type="Full-time",
    description="We are looking for a senior engineer...",
    posted_date=datetime.now(),
    link="https://linkedin.com/jobs/12345",
    platform="linkedin"
)
```

**Fields:**
- `company_name` (str, required): Name of the company
- `job_title` (str, required): Job title/position
- `job_type` (str, optional): Employment type (e.g., "Full-time", "Part-time", "Contract")
- `description` (str, required): Full job description text
- `posted_date` (datetime, optional): When the job was posted
- `link` (str, optional): URL to the job posting
- `platform` (str, required): Source platform ("linkedin", "indeed", "glassdoor")

### Platform-Specific Models

Internal models for platform-specific parsing:

- `LinkedInJob`: Parses LinkedIn raw job data
- `IndeedJob`: Parses Indeed raw job data
- `GlassdoorJob`: Parses Glassdoor raw job data

All have a `.to_job_posting()` method to convert to the standard `JobPosting` model.

### JobSearchResult & JobSearchResults

Aggregate models for managing results across multiple platforms:

```python
from autoapply.models import JobSearchResults

results = JobSearchResults()
results.add_result("linkedin", linkedin_jobs)
results.add_result("indeed", indeed_jobs)

total = results.total_jobs
all_jobs = results.get_all_jobs()
```

## Usage Examples

### Converting Platform Jobs to Pydantic

```python
from autoapply.utils.job_converter import convert_jobs_by_platform

# Raw jobs from LinkedIn scraper
raw_linkedin_jobs = [
    {
        "title": "Python Developer",
        "company": "Tech Corp",
        "link": "https://...",
        "content": "Job description..."
    }
]

# Convert to validated Pydantic models
jobs = convert_jobs_by_platform("linkedin", raw_linkedin_jobs)

for job in jobs:
    print(f"{job.job_title} @ {job.company_name}")
```

### Filtering Jobs

```python
all_jobs = results.get_all_jobs()

# Filter by job type
fulltime = [j for j in all_jobs if j.job_type == "Full-time"]

# Filter by platform
linkedin_jobs = [j for j in all_jobs if j.platform == "linkedin"]

# Search in description
python_jobs = [j for j in all_jobs if "python" in j.description.lower()]
```

### Exporting to JSON

```python
# Single job
job_json = job.model_dump_json(indent=2)

# All results
results_json = results.model_dump_json(indent=2)

# Save to file
with open("jobs.json", "w") as f:
    f.write(results_json)
```

### Validation

Pydantic automatically validates data:

```python
from pydantic import ValidationError

try:
    invalid_job = JobPosting(
        company_name="",  # Will fail - must be non-empty
        job_title="Title",
        description="Desc",
        platform="linkedin"
    )
except ValidationError as e:
    print(e)
```

## Integration with Platform Scrapers

After scraping jobs, convert them before saving:

```python
# In platform's search_jobs() method
raw_jobs = await scrape_jobs()  # Returns List[Dict]
validated_jobs = convert_jobs_by_platform("linkedin", raw_jobs)

# Now use validated_jobs for saving/filtering
return validated_jobs
```

## File Structure

```
src/autoapply/
├── models.py                    # Pydantic model definitions
└── utils/
    └── job_converter.py         # Conversion utilities

examples/
└── pydantic_jobs_example.py     # Usage examples
```

## See Also

- Run examples: `python examples/pydantic_jobs_example.py`
- Pydantic docs: https://docs.pydantic.dev/
