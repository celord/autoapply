"""
Test configuration loading functionality
"""

from pathlib import Path
import pytest
from autoapply.utils.config_loader import ConfigLoader


@pytest.fixture
def config_path():
    """Fixture to provide the path to the config file."""
    return Path(__file__).parent.parent / "config" / "config.toml"


def test_config_loader_initialization(config_path):
    """Test that ConfigLoader can be initialized with a valid config file."""
    loader = ConfigLoader(config_path)
    assert loader is not None
    assert loader.config is not None


def test_config_required_sections(config_path):
    """Test that all required configuration sections are present."""
    loader = ConfigLoader(config_path)
    required_sections = [
        "search",
        "application",
        "platforms",
        "browser",
        "delays",
        "logging",
    ]

    for section in required_sections:
        assert section in loader.config


def test_search_settings(config_path):
    """Test that search settings are properly configured."""
    loader = ConfigLoader(config_path)
    search_config = loader.config["search"]

    assert "keywords" in search_config
    assert "location" in search_config
    assert "experience_level" in search_config
    assert isinstance(search_config["keywords"], str)
    assert isinstance(search_config["location"], str)


def test_platform_settings(config_path):
    """Test that platform settings are properly configured."""
    loader = ConfigLoader(config_path)
    platforms_config = loader.config["platforms"]

    for platform in ["linkedin", "indeed", "glassdoor"]:
        assert platform in platforms_config
        assert "enabled" in platforms_config[platform]
        assert isinstance(platforms_config[platform]["enabled"], bool)
        assert "search_limit" in platforms_config[platform]
        assert isinstance(platforms_config[platform]["search_limit"], int)


def test_config_get_method(config_path):
    """Test the get method for accessing configuration values."""
    loader = ConfigLoader(config_path)

    # Test existing key
    assert loader.get("search.keywords") == "Python Developer"

    # Test nested key
    assert isinstance(loader.get("platforms.linkedin.enabled"), bool)

    # Test non-existent key
    assert loader.get("non.existent.key", default="default") == "default"


def test_config_update_method(config_path):
    """Test the update method for modifying configuration values."""
    loader = ConfigLoader(config_path)

    # Update a value
    new_keywords = "Senior Python Developer"
    loader.update("search.keywords", new_keywords)
    assert loader.get("search.keywords") == new_keywords

    # Update nested value
    loader.update("platforms.linkedin.search_limit", 200)
    assert loader.get("platforms.linkedin.search_limit") == 200
