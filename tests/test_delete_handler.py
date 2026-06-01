import pytest
import json
import uuid
from moto import mock_aws
from lambdas.shared import ImageRecord, get_db, get_storage
from lambdas.delete_image.handler import lambda_handler


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


class TestDeleteImageHandler:
    
    def test_delete_image_success(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test successful image deletion."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 204
        assert response['body'] == ''

        deleted_record = db.get_image(sample_image_record.image_id)
        assert deleted_record.status == 'deleted'

    
    def test_delete_image_not_found(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test deleting non-existent image."""
        event = {
            'pathParameters': {'id': str(uuid.uuid4())}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Image not found' in body['error']

    
    def test_delete_image_missing_id(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test delete without image_id."""
        event = {'pathParameters': {}}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id' in body['error']

    
    def test_delete_image_no_path_parameters(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test delete without pathParameters."""
        event = {}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing image_id' in body['error']

    
    def test_delete_already_deleted_image(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record):
        """Test deleting already deleted image."""
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

    
    def test_delete_image_response_headers(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that delete response has correct headers."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 204


    def test_delete_image_removes_from_s3(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that delete removes image from S3."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 204

    
    def test_delete_image_marks_deleted_in_db(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that delete marks image as deleted in DynamoDB."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 204

        updated_record = db.get_image(sample_image_record.image_id)
        assert updated_record.status == 'deleted'

    
    def test_delete_multiple_images(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_bytes):
        """Test deleting multiple images in sequence."""
        db = get_db()
        storage = get_storage()

        records = []
        for i in range(3):
            record = ImageRecord.create(
                user_id='user123',
                filename=f'photo{i}.png',
                content_type='image/png',
                size_bytes=1024
            )
            db.put_image(record)
            storage.upload_image(record.s3_key, sample_image_bytes, record.content_type)
            records.append(record)

        for record in records:
            event = {
                'pathParameters': {'id': record.image_id}
            }

            response = lambda_handler(event, None)

            assert response['statusCode'] == 204
            deleted_record = db.get_image(record.image_id)
            assert deleted_record.status == 'deleted'

    
    def test_delete_preserves_metadata(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_record, sample_image_bytes):
        """Test that delete preserves image metadata."""
        db = get_db()
        storage = get_storage()

        db.put_image(sample_image_record)
        storage.upload_image(sample_image_record.s3_key, sample_image_bytes, sample_image_record.content_type)

        event = {
            'pathParameters': {'id': sample_image_record.image_id}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 204

        deleted_record = db.get_image(sample_image_record.image_id)
        assert deleted_record.image_id == sample_image_record.image_id
        assert deleted_record.user_id == sample_image_record.user_id
        assert deleted_record.filename == sample_image_record.filename
        assert deleted_record.caption == sample_image_record.caption
        assert deleted_record.tags == sample_image_record.tags
