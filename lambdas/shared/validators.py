import base64
import uuid
from datetime import datetime
from .exceptions import ValidationError

ALLOWED_CONTENT_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
}


def validate_content_type(content_type):
    """Validate that content type is in the allowed list."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported content_type: {content_type}. "
            f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )


def validate_base64(data_str):
    """Validate that string is valid base64 and return decoded bytes."""
    try:
        return base64.b64decode(data_str, validate=True)
    except Exception as e:
        raise ValidationError(f"Invalid base64 data: {str(e)}")


def parse_iso_date(date_str):
    """Parse ISO-8601 date string to datetime object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValidationError(f"Invalid ISO-8601 date format: {date_str}. Error: {str(e)}")


def validate_uuid(value):
    """Validate that value is a valid UUID."""
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValidationError(f"Invalid UUID format: {value}")


def validate_required_field(data, field_name):
    """Validate that a required field is present and non-empty."""
    if field_name not in data or not data[field_name]:
        raise ValidationError(f"Missing required field: {field_name}")
    return data[field_name]
