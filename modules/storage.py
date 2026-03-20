"""
Data Storage Utilities
=======================
Handles data persistence and serialization for harvested data.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def json_serializer(obj: Any) -> str:
    """
    JSON serializer for objects not serializable by default.

    Handles datetime, sets, and other non-standard types.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, '__dict__'):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def ensure_output_dir(output_dir: str) -> Path:
    """
    Ensure output directory exists.

    Args:
        output_dir: Directory path to create

    Returns:
        Path object for the directory
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(output_dir: str, handle: str, suffix: str = "_raw") -> Path:
    """
    Get the output file path for a harvested profile.

    Args:
        output_dir: Directory for output
        handle: GitHub handle
        suffix: Filename suffix (e.g., "_raw", "_profile")

    Returns:
        Path object for the output file
    """
    path = ensure_output_dir(output_dir)
    return path / f"{handle}{suffix}.json"


def save_json(data: Dict[str, Any], output_path: Path, indent: int = 2) -> bool:
    """
    Save data to JSON file with proper serialization.

    Args:
        data: Dictionary to save
        output_path: Path to save file
        indent: JSON indentation level

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=json_serializer)
        logger.info(f"Data saved to {output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to save data to {output_path}: {e}")
        return False
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        return False


def load_json(input_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load data from JSON file.

    Args:
        input_path: Path to JSON file

    Returns:
        Dictionary loaded from file, or None if failed
    """
    if not input_path.exists():
        logger.warning(f"File not found: {input_path}")
        return None

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        logger.error(f"Failed to read {input_path}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {input_path}: {e}")
        return None


def save_harvested_data(
    data: Dict[str, Any],
    output_dir: str,
    handle: str,
    suffix: str = "_raw"
) -> Optional[Path]:
    """
    Save harvested data to file.

    Args:
        data: Harvested data dictionary
        output_dir: Output directory
        handle: GitHub handle
        suffix: Filename suffix

    Returns:
        Path to saved file, or None if failed
    """
    output_path = get_output_path(output_dir, handle, suffix)
    if save_json(data, output_path):
        return output_path
    return None


def save_metadata(
    metadata: Dict[str, Any],
    output_dir: str,
    handle: str
) -> Optional[Path]:
    """
    Save metadata separately for quick access.

    Args:
        metadata: Metadata dictionary
        output_dir: Output directory
        handle: GitHub handle

    Returns:
        Path to saved metadata file, or None if failed
    """
    output_path = get_output_path(output_dir, handle, "_metadata")
    return output_path if save_json(metadata, output_path) else None


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB, or 0 if file doesn't exist
    """
    if file_path.exists():
        return file_path.stat().st_size / (1024 * 1024)
    return 0.0


def validate_harvested_data(data: Dict[str, Any]) -> bool:
    """
    Validate that harvested data has required fields.

    Args:
        data: Harvested data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ['github_handle', 'user', 'repos', 'metadata']

    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return False

    return True
