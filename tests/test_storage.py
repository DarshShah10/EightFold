"""
Tests for Storage Module
========================
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.storage import (
    json_serializer,
    ensure_output_dir,
    get_output_path,
    save_json,
    load_json,
    save_harvested_data,
    get_file_size_mb,
    validate_harvested_data,
)


class TestJsonSerializer:
    """Tests for json_serializer function."""

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = json_serializer(dt)
        assert result == "2024-01-15T10:30:00"

    def test_serialize_set(self):
        """Test set serialization."""
        s = {1, 2, 3}
        result = json_serializer(s)
        assert isinstance(result, list)
        assert set(result) == {1, 2, 3}

    def test_serialize_unknown_type(self):
        """Test that objects with __dict__ are serialized as strings."""
        class UnknownType:
            pass

        # Objects with __dict__ are serialized as strings
        result = json_serializer(UnknownType())
        assert isinstance(result, str)


class TestEnsureOutputDir:
    """Tests for ensure_output_dir function."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new_data"
        result = ensure_output_dir(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test with existing directory."""
        result = ensure_output_dir(str(tmp_path))
        assert tmp_path.exists()


class TestGetOutputPath:
    """Tests for get_output_path function."""

    def test_default_suffix(self, tmp_path):
        """Test default suffix."""
        path = get_output_path(str(tmp_path), "testuser")
        assert path.name == "testuser_raw.json"

    def test_custom_suffix(self, tmp_path):
        """Test custom suffix."""
        path = get_output_path(str(tmp_path), "testuser", "_profile")
        assert path.name == "testuser_profile.json"


class TestSaveJson:
    """Tests for save_json function."""

    def test_save_simple_data(self, tmp_path):
        """Test saving simple data."""
        data = {"name": "test", "value": 42}
        output_path = tmp_path / "test.json"

        result = save_json(data, output_path)
        assert result is True
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_with_datetime(self, tmp_path):
        """Test saving data with datetime."""
        data = {"created": datetime(2024, 1, 15, 10, 30, 0)}
        output_path = tmp_path / "test.json"

        result = save_json(data, output_path)
        assert result is True

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["created"] == "2024-01-15T10:30:00"

    def test_save_with_sets(self, tmp_path):
        """Test saving data with sets."""
        data = {"tags": {"python", "testing"}}
        output_path = tmp_path / "test.json"

        result = save_json(data, output_path)
        assert result is True

        with open(output_path) as f:
            loaded = json.load(f)
        assert set(loaded["tags"]) == {"python", "testing"}

    def test_save_failure(self, tmp_path):
        """Test handling of save failure."""
        # Try to save to invalid path
        data = {"test": "data"}
        output_path = Path("/invalid/path/test.json")

        result = save_json(data, output_path)
        assert result is False


class TestLoadJson:
    """Tests for load_json function."""

    def test_load_existing_file(self, tmp_path):
        """Test loading existing file."""
        data = {"name": "test", "value": 42}
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))

        loaded = load_json(file_path)
        assert loaded == data

    def test_load_missing_file(self, tmp_path):
        """Test loading non-existent file."""
        file_path = tmp_path / "missing.json"
        loaded = load_json(file_path)
        assert loaded is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")

        loaded = load_json(file_path)
        assert loaded is None


class TestSaveHarvestedData:
    """Tests for save_harvested_data function."""

    def test_save_with_handle(self, tmp_path):
        """Test saving with handle."""
        data = {"github_handle": "testuser", "value": 42}
        output_path = save_harvested_data(data, str(tmp_path), "testuser")

        assert output_path is not None
        assert output_path.exists()
        assert output_path.name == "testuser_raw.json"


class TestGetFileSizeMb:
    """Tests for get_file_size_mb function."""

    def test_existing_file(self, tmp_path):
        """Test getting size of existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * (1024 * 1024))  # 1 MB

        size = get_file_size_mb(test_file)
        assert 0.9 < size < 1.1  # Allow some variance

    def test_missing_file(self, tmp_path):
        """Test getting size of missing file."""
        file_path = tmp_path / "missing.txt"
        size = get_file_size_mb(file_path)
        assert size == 0.0


class TestValidateHarvestedData:
    """Tests for validate_harvested_data function."""

    def test_valid_data(self, sample_raw_data):
        """Test validation of valid data."""
        result = validate_harvested_data(sample_raw_data)
        assert result is True

    def test_missing_github_handle(self, sample_raw_data):
        """Test validation with missing handle."""
        del sample_raw_data["github_handle"]
        result = validate_harvested_data(sample_raw_data)
        assert result is False

    def test_missing_user(self, sample_raw_data):
        """Test validation with missing user."""
        del sample_raw_data["user"]
        result = validate_harvested_data(sample_raw_data)
        assert result is False

    def test_missing_repos(self, sample_raw_data):
        """Test validation with missing repos."""
        del sample_raw_data["repos"]
        result = validate_harvested_data(sample_raw_data)
        assert result is False

    def test_missing_metadata(self, sample_raw_data):
        """Test validation with missing metadata."""
        del sample_raw_data["metadata"]
        result = validate_harvested_data(sample_raw_data)
        assert result is False
