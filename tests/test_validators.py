import pytest
import base64
from datetime import datetime
from lambdas.shared import (
    validate_content_type,
    validate_base64,
    parse_iso_date,
    validate_uuid,
    validate_required_field,
    ValidationError
)


class TestValidateContentType:
    def test_valid_jpeg(self):
        """Test valid JPEG content type."""
        validate_content_type('image/jpeg')

    def test_valid_png(self):
        """Test valid PNG content type."""
        validate_content_type('image/png')

    def test_valid_gif(self):
        """Test valid GIF content type."""
        validate_content_type('image/gif')

    def test_valid_webp(self):
        """Test valid WebP content type."""
        validate_content_type('image/webp')

    def test_invalid_content_type(self):
        """Test invalid content type."""
        with pytest.raises(ValidationError) as excinfo:
            validate_content_type('image/bmp')
        assert 'Unsupported content_type' in str(excinfo.value)

    def test_text_content_type(self):
        """Test non-image content type."""
        with pytest.raises(ValidationError):
            validate_content_type('text/plain')


class TestValidateBase64:
    def test_valid_base64(self):
        """Test valid base64 string."""
        original = b"test data"
        encoded = base64.b64encode(original).decode('utf-8')
        result = validate_base64(encoded)
        assert result == original

    def test_invalid_base64(self):
        """Test invalid base64 string."""
        with pytest.raises(ValidationError) as excinfo:
            validate_base64("not@valid!base64!")
        assert 'Invalid base64 data' in str(excinfo.value)

    def test_empty_base64(self):
        """Test empty base64 string."""
        result = validate_base64("")
        assert result == b""

    def test_large_base64(self):
        """Test large base64 string."""
        large_data = b"x" * 10000
        encoded = base64.b64encode(large_data).decode('utf-8')
        result = validate_base64(encoded)
        assert result == large_data


class TestParseIsoDate:
    def test_valid_iso_date_with_z(self):
        """Test parsing ISO-8601 date with Z suffix."""
        date_str = "2024-01-15T10:30:00Z"
        result = parse_iso_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_valid_iso_date_with_timezone(self):
        """Test parsing ISO-8601 date with timezone."""
        date_str = "2024-01-15T10:30:00+00:00"
        result = parse_iso_date(date_str)
        assert isinstance(result, datetime)

    def test_valid_iso_date_without_time(self):
        """Test parsing ISO-8601 date without time."""
        date_str = "2024-01-15"
        result = parse_iso_date(date_str)
        assert isinstance(result, datetime)

    def test_invalid_iso_date(self):
        """Test parsing invalid ISO-8601 date."""
        with pytest.raises(ValidationError) as excinfo:
            parse_iso_date("2024-13-45")
        assert 'Invalid ISO-8601 date format' in str(excinfo.value)

    def test_none_date(self):
        """Test parsing None date."""
        result = parse_iso_date(None)
        assert result is None

    def test_empty_string_date(self):
        """Test parsing empty string date."""
        result = parse_iso_date("")
        assert result is None


class TestValidateUuid:
    def test_valid_uuid(self):
        """Test valid UUID."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        result = validate_uuid(uuid_str)
        assert result == uuid_str

    def test_invalid_uuid(self):
        """Test invalid UUID."""
        with pytest.raises(ValidationError) as excinfo:
            validate_uuid("not-a-uuid")
        assert 'Invalid UUID format' in str(excinfo.value)

    def test_uuid_wrong_format(self):
        """Test UUID with empty string."""
        with pytest.raises(ValidationError):
            validate_uuid("")


class TestValidateRequiredField:
    def test_valid_required_field(self):
        """Test validating present required field."""
        data = {'name': 'John'}
        result = validate_required_field(data, 'name')
        assert result == 'John'

    def test_missing_required_field(self):
        """Test validating missing required field."""
        data = {'email': 'john@example.com'}
        with pytest.raises(ValidationError) as excinfo:
            validate_required_field(data, 'name')
        assert 'Missing required field: name' in str(excinfo.value)

    def test_empty_required_field(self):
        """Test validating empty required field."""
        data = {'name': ''}
        with pytest.raises(ValidationError) as excinfo:
            validate_required_field(data, 'name')
        assert 'Missing required field: name' in str(excinfo.value)

    def test_none_required_field(self):
        """Test validating None required field."""
        data = {'name': None}
        with pytest.raises(ValidationError):
            validate_required_field(data, 'name')

    def test_numeric_required_field(self):
        """Test validating numeric required field."""
        data = {'age': 25}
        result = validate_required_field(data, 'age')
        assert result == 25

    def test_zero_numeric_field_is_falsy(self):
        """Test that zero is considered falsy."""
        data = {'count': 0}
        with pytest.raises(ValidationError):
            validate_required_field(data, 'count')
