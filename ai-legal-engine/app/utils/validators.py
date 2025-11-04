"""
app/utils/validators.py

Reusable custom validators for Pydantic and domain-specific validation
"""

import re
from typing import Any, List


def validate_email(value: str) -> str:
    """Validate that a string is a properly formatted email address."""
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, value):
        raise ValueError(f"Invalid email format: {value}")
    return value


def validate_token(value: str) -> str:
    """Validate a token string to be alphanumeric with dashes/underscores, length 10-50."""
    if not isinstance(value, str):
        raise ValueError("Token must be a string")
    if not (10 <= len(value) <= 50):
        raise ValueError("Token length must be between 10 and 50 characters")
    if not re.match(r"^[a-zA-Z0-9_-]+$", value):
        raise ValueError("Token must contain only letters, numbers, underscores or dashes")
    return value


def validate_enum(value: Any, allowed_values: List[Any], field_name: str = "Value") -> Any:
    """Validate a value is one of an allowed set."""
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}, got '{value}'")
    return value


def validate_non_empty_str(value: str) -> str:
    """Validate a string is not empty or whitespace only."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("String value cannot be empty or whitespace")
    return value.strip()


def validate_url(value: str) -> str:
    """Basic URL validator."""
    url_regex = (
        r"^(?:http|ftp)s?://"  # http:// or https:// or ftp://
        r"(?:\S+(?::\S*)?@)?"  # user and pass
        r"(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}\."  # IP v4
        r"(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4])|"  # last octet
        r"(?:(?:[a-z\u00a1-\uffff0-9]-*)*"  # domain name part
        r"[a-z\u00a1-\uffff0-9]+)"  # domain name part
        r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"  # TLD
        r"\.?)"  # dot
        r"(?::\d{2,5})?"  # port
        r"(?:[/?#]\S*)?$", re.IGNORECASE
    )
    if not re.match(url_regex, value):
        raise ValueError("Invalid URL format")
    return value


# Additional domain-specific validators can be added here as needed
