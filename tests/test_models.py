import pytest
from datetime import datetime
from lambdas.shared import ImageRecord


class TestImageRecord:
    def test_create_basic(self):
        """Test creating an ImageRecord with minimal fields."""
        record = ImageRecord.create(
            user_id="user123",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024
        )

        assert record.user_id == "user123"
        assert record.filename == "photo.jpg"
        assert record.content_type == "image/jpeg"
        assert record.size_bytes == 1024
        assert record.status == "active"
        assert record.tags == set()
        assert record.caption is None
        assert record.image_id is not None
        assert record.s3_key.startswith("users/user123/")
        assert record.uploaded_at is not None

    def test_create_with_tags_and_caption(self):
        """Test creating an ImageRecord with tags and caption."""
        tags = ["nature", "landscape"]
        caption = "Beautiful sunset"

        record = ImageRecord.create(
            user_id="user456",
            filename="sunset.png",
            content_type="image/png",
            size_bytes=2048,
            tags=tags,
            caption=caption
        )

        assert record.tags == set(tags)
        assert record.caption == caption

    def test_s3_key_format(self):
        """Test that S3 key is properly formatted."""
        record = ImageRecord.create(
            user_id="user789",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024
        )

        expected_prefix = "users/user789/"
        assert record.s3_key.startswith(expected_prefix)
        assert record.s3_key.endswith("/photo.jpg")

    def test_to_dynamo_item(self):
        """Test converting ImageRecord to DynamoDB item format."""
        record = ImageRecord.create(
            user_id="user123",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            tags=["tag1", "tag2"],
            caption="Test caption"
        )

        item = record.to_dynamo_item()

        assert item['image_id'] == record.image_id
        assert item['user_id'] == "user123"
        assert item['filename'] == "photo.jpg"
        assert item['content_type'] == "image/jpeg"
        assert item['size_bytes'] == 1024
        assert item['status'] == 'active'
        assert item['caption'] == "Test caption"
        assert item['tags'] == {"tag1", "tag2"}

    def test_to_dynamo_item_without_optional_fields(self):
        """Test converting ImageRecord to DynamoDB without optional fields."""
        record = ImageRecord.create(
            user_id="user123",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024
        )

        item = record.to_dynamo_item()

        assert 'caption' not in item
        assert 'tags' not in item

    def test_from_dynamo_item(self):
        """Test converting DynamoDB item to ImageRecord."""
        item = {
            'image_id': 'img123',
            'user_id': 'user123',
            's3_key': 'users/user123/img123/photo.jpg',
            'filename': 'photo.jpg',
            'content_type': 'image/jpeg',
            'size_bytes': 1024,
            'uploaded_at': '2024-01-01T12:00:00Z',
            'status': 'active',
            'tags': {'tag1', 'tag2'},
            'caption': 'Test caption'
        }

        record = ImageRecord.from_dynamo_item(item)

        assert record.image_id == 'img123'
        assert record.user_id == 'user123'
        assert record.filename == 'photo.jpg'
        assert record.tags == {'tag1', 'tag2'}
        assert record.caption == 'Test caption'

    def test_from_dynamo_item_missing_optional_fields(self):
        """Test converting DynamoDB item without optional fields."""
        item = {
            'image_id': 'img123',
            'user_id': 'user123',
            's3_key': 'users/user123/img123/photo.jpg',
            'filename': 'photo.jpg',
            'content_type': 'image/jpeg',
            'size_bytes': 1024,
            'uploaded_at': '2024-01-01T12:00:00Z'
        }

        record = ImageRecord.from_dynamo_item(item)

        assert record.status == 'active'
        assert record.tags == set()
        assert record.caption is None

    def test_to_json(self):
        """Test converting ImageRecord to JSON-serializable dict."""
        record = ImageRecord.create(
            user_id="user123",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024,
            tags=["tag1", "tag2"],
            caption="Test caption"
        )

        json_data = record.to_json()

        assert json_data['image_id'] == record.image_id
        assert json_data['user_id'] == "user123"
        assert json_data['filename'] == "photo.jpg"
        assert json_data['tags'] == ["tag1", "tag2"]  # Sorted list
        assert json_data['caption'] == "Test caption"
        assert json_data['status'] == 'active'

    def test_to_json_empty_tags(self):
        """Test to_json with empty tags."""
        record = ImageRecord.create(
            user_id="user123",
            filename="photo.jpg",
            content_type="image/jpeg",
            size_bytes=1024
        )

        json_data = record.to_json()

        assert json_data['tags'] == []
        assert 'caption' not in json_data
