"""
Security Utilities for SQL Injection Prevention

This module provides defense-in-depth against SQL injection attacks.
SQLAlchemy ORM already uses parameterized queries, but these utilities
add an extra layer of input validation and sanitization.
"""

import re
from typing import Any, Optional
from fastapi import HTTPException, status


# SQL keywords that should never appear in user input fields
SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
    "ALTER", "CREATE", "REPLACE", "EXEC", "EXECUTE", "UNION",
    "INTO", "WHERE", "FROM", "JOIN", "OR", "AND", "--", ";",
    "/*", "*/", "CHAR(", "CONCAT(", "0x", "INFORMATION_SCHEMA",
    "SLEEP(", "BENCHMARK(", "LOAD_FILE(", "OUTFILE"
]

# Regex patterns for detecting injection attempts
INJECTION_PATTERNS = [
    r"[\'\"];\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)",  # String termination + SQL
    r"--\s*$",  # SQL comment at end
    r"/\*.*\*/",  # Block comment
    r"[\'\"](\s*OR\s*|\s*AND\s*)[\'\"]?\d*[\'\"]?\s*=\s*[\'\"]?\d*",  # OR/AND injection
    r"UNION\s+(ALL\s+)?SELECT",  # UNION injection
    r"0x[0-9a-fA-F]+",  # Hex encoding
    r"CHAR\s*\(",  # Char encoding
    r";\s*DROP\s+TABLE",  # DROP TABLE
    r";\s*TRUNCATE\s+TABLE",  # TRUNCATE TABLE
    r"xp_",  # SQL Server extended procedures
]


def detect_sql_injection(value: str) -> bool:
    """
    Detect potential SQL injection attempts in a string value.
    
    Returns True if injection is detected, False otherwise.
    """
    if not isinstance(value, str):
        return False
    
    upper_value = value.upper()
    
    # Check for SQL keywords
    for keyword in SQL_KEYWORDS:
        if keyword.upper() in upper_value:
            # Additional check: is it surrounded by valid context?
            # For names like "Anderson" containing "AND", we don't want false positives
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, upper_value, re.IGNORECASE):
                # Found as a standalone word, likely malicious
                # But exclude common false positives
                if keyword in ["OR", "AND", "INTO", "FROM", "WHERE"]:
                    # These need additional context to be suspicious
                    if re.search(r"[\'\"];", value) or re.search(r"=\s*[\'\"]", value):
                        return True
                elif keyword == "--":
                    if re.search(r"--\s*$", value):
                        return True
                else:
                    return True
    
    # Check regex patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return True
    
    return False


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.
    
    This is a secondary defense after parameterized queries.
    """
    if not isinstance(value, str):
        return str(value)
    
    # Truncate to max length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Remove backslash escapes that could interfere
    value = re.sub(r"\\[\'\"nrtbf0]", "", value)
    
    return value.strip()


def validate_uuid_format(value: str) -> bool:
    """Validate that a string is a valid UUID format."""
    uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    return bool(re.match(uuid_pattern, value))


def validate_name(name: str) -> str:
    """
    Validate and sanitize a name field.
    
    Names should contain only letters, spaces, and basic punctuation.
    """
    if not name or not isinstance(name, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid name provided"
        )
    
    name = sanitize_string(name, max_length=100)
    
    if detect_sql_injection(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters detected in name"
        )
    
    # Only allow letters, spaces, hyphens, apostrophes, and periods
    if not re.match(r"^[\w\s\.\'\-]+$", name, re.UNICODE):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name contains invalid characters"
        )
    
    return name


def validate_place(place: str) -> str:
    """
    Validate and sanitize a place/city field.
    """
    if not place or not isinstance(place, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid place provided"
        )
    
    place = sanitize_string(place, max_length=200)
    
    if detect_sql_injection(place):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters detected in place"
        )
    
    return place


def validate_date_format(date_str: str) -> str:
    """Validate ISO date format (YYYY-MM-DD)."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    return date_str


def validate_time_format(time_str: str) -> str:
    """Validate time format (HH:MM or HH:MM:SS)."""
    if not re.match(r"^\d{2}:\d{2}(:\d{2})?$", time_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    return time_str


def validate_latitude(lat: float) -> float:
    """Validate latitude range."""
    if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90"
        )
    return float(lat)


def validate_longitude(lon: float) -> float:
    """Validate longitude range."""
    if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180"
        )
    return float(lon)


def validate_input(value: Any, field_name: str = "input") -> Any:
    """
    General input validation for any string field.
    
    Raises HTTPException if SQL injection is detected.
    """
    if isinstance(value, str):
        if detect_sql_injection(value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid characters detected in {field_name}"
            )
    return value
