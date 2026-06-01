import pytest
import json
import base64
import uuid
from moto import mock_aws
from lambdas.shared import ImageRecord, get_db, get_storage
from lambdas.get_image.handler import lambda_handler


@pytest.fixture
def sample_image_record():
    """Create a sample image record."""
    return ImageRecord.create(
        user_id='user123',
        filename='photo.png',
        content_type='image/png',
        size_bytes=1024,
        tags=['nature'],
        caption='Beautiful view'
    )


class TestGetImageHandler:
    
    def test_get_image_success(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test successful get image."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['image_id'] == sample_image_record.image_id
        assert body['user_id'] == 'user123'
        assert body['filename'] == 'photo.png'
        assert 'download_url' in body
        assert body['download_url'].startswith('http')

    
    def test_get_image_not_found(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test get non-existent image."""
        event = {
            'pathParameters': {'id': str(uuid.uuid4())}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Image not found' in body['error']

    
    def test_get_image_missing_id(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test get image without image_id."""
        event = {'pathParameters': {}}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id' in body['error']

    
    def test_get_image_no_path_parameters(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test get image without pathParameters."""
        event = {}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id' in body['error']

    
    def test_get_deleted_image(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record):
        """Test get deleted image returns 404."""
        db = get_db()
        record = sample_image_record
        record.status = 'deleted'
        db.put_image(record)

        event = {
            'pathParameters': {'id': record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Image not found' in body['error']

    
    def test_get_image_response_contains_metadata(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that get image response includes all metadata."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['size_bytes'] == 1024
        assert body['status'] == 'active'
        assert body['caption'] == 'Beautiful view'
        assert set(body['tags']) == {'nature'}

    
    def test_get_image_response_headers(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that get image response has correct headers."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['headers']['Content-Type'] == 'application/json'

    
    def test_get_image_presigned_url_validity(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that presigned URL is a valid S3 URL."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        body = json.loads(response['body'])
        download_url = body['download_url']
        assert 'instagram-images' in download_url
        assert sample_image_record.s3_key in download_url
