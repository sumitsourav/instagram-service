import pytest
import json
import base64
import uuid
from datetime import datetime, timedelta
from moto import mock_aws
from lambdas.shared import ImageRecord, get_db
from lambdas.list_images.handler import lambda_handler


class TestListImagesHandler:
    
    def test_list_images_by_user_id(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images by user_id."""
        db = get_db()

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024,
            tags=['nature']
        )
        record2 = ImageRecord.create(
            user_id='user123',
            filename='photo2.jpg',
            content_type='image/jpeg',
            size_bytes=2048,
            tags=['landscape']
        )
        record3 = ImageRecord.create(
            user_id='user456',
            filename='photo3.png',
            content_type='image/png',
            size_bytes=1024
        )

        db.put_image(record1)
        db.put_image(record2)
        db.put_image(record3)

        event = {
            'queryStringParameters': {'user_id': 'user123'}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert len(body['images']) == 2
        assert all(img['user_id'] == 'user123' for img in body['images'])

    
    def test_list_images_by_content_type(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images by content_type."""
        db = get_db()

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024
        )
        record2 = ImageRecord.create(
            user_id='user456',
            filename='photo2.png',
            content_type='image/png',
            size_bytes=2048
        )
        record3 = ImageRecord.create(
            user_id='user789',
            filename='photo3.jpg',
            content_type='image/jpeg',
            size_bytes=1024
        )

        db.put_image(record1)
        db.put_image(record2)
        db.put_image(record3)

        event = {
            'queryStringParameters': {'content_type': 'image/png'}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2
        assert all(img['content_type'] == 'image/png' for img in body['images'])

    
    def test_list_all_images(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing all images without filters."""
        db = get_db()

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024
        )
        record2 = ImageRecord.create(
            user_id='user456',
            filename='photo2.jpg',
            content_type='image/jpeg',
            size_bytes=2048
        )

        db.put_image(record1)
        db.put_image(record2)

        event = {
            'queryStringParameters': {}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2

    
    def test_list_images_with_tag_filter(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with tag filter."""
        db = get_db()

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024,
            tags=['nature', 'landscape']
        )
        record2 = ImageRecord.create(
            user_id='user123',
            filename='photo2.jpg',
            content_type='image/jpeg',
            size_bytes=2048,
            tags=['city']
        )

        db.put_image(record1)
        db.put_image(record2)

        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'tag': 'nature'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert 'nature' in body['images'][0]['tags']

    
    def test_list_images_with_date_filter(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with date range filter."""
        db = get_db()

        now = datetime.utcnow()
        yesterday = (now - timedelta(days=1)).isoformat() + 'Z'
        tomorrow = (now + timedelta(days=1)).isoformat() + 'Z'

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024
        )
        record2 = ImageRecord.create(
            user_id='user123',
            filename='photo2.jpg',
            content_type='image/jpeg',
            size_bytes=2048
        )

        db.put_image(record1)
        db.put_image(record2)

        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'date_from': yesterday,
                'date_to': tomorrow
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2

    
    def test_list_images_with_limit(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with limit."""
        db = get_db()

        for i in range(5):
            record = ImageRecord.create(
                user_id='user123',
                filename=f'photo{i}.png',
                content_type='image/png',
                size_bytes=1024
            )
            db.put_image(record)

        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '2'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 2

    
    def test_list_images_pagination(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with pagination."""
        db = get_db()

        for i in range(5):
            record = ImageRecord.create(
                user_id='user123',
                filename=f'photo{i}.png',
                content_type='image/png',
                size_bytes=1024
            )
            db.put_image(record)

        event1 = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '2'
            }
        }

        response1 = lambda_handler(event1, None)
        assert response1['statusCode'] == 200
        body1 = json.loads(response1['body'])
        assert body1['count'] == 2
        assert 'next_page_token' in body1

        next_token = body1['next_page_token']
        event2 = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '2',
                'last_evaluated_key': next_token
            }
        }

        response2 = lambda_handler(event2, None)
        assert response2['statusCode'] == 200
        body2 = json.loads(response2['body'])
        assert body2['count'] == 2

    
    def test_list_images_invalid_limit(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with invalid limit."""
        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '101'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'limit must be between 1 and 100' in body['error']

    
    def test_list_images_invalid_limit_zero(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with limit of 0."""
        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '0'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    
    def test_list_images_invalid_limit_negative(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with negative limit."""
        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': '-5'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400

    
    def test_list_images_invalid_limit_not_number(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with non-numeric limit."""
        event = {
            'queryStringParameters': {
                'user_id': 'user123',
                'limit': 'abc'
            }
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    
    def test_list_images_deleted_not_returned(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test that deleted images are not returned."""
        db = get_db()

        record1 = ImageRecord.create(
            user_id='user123',
            filename='photo1.png',
            content_type='image/png',
            size_bytes=1024
        )
        record2 = ImageRecord.create(
            user_id='user123',
            filename='photo2.jpg',
            content_type='image/jpeg',
            size_bytes=2048
        )
        record2.status = 'deleted'

        db.put_image(record1)
        db.put_image(record2)

        event = {
            'queryStringParameters': {'user_id': 'user123'}
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
        assert body['images'][0]['image_id'] == record1.image_id

    
    def test_list_images_newest_first(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test that images are returned newest first."""
        db = get_db()

        for i in range(3):
            record = ImageRecord.create(
                user_id='user123',
                filename=f'photo{i}.png',
                content_type='image/png',
                size_bytes=1024
            )
            db.put_image(record)

        event = {
            'queryStringParameters': {'user_id': 'user123'}
        }

        response = lambda_handler(event, None)

        body = json.loads(response['body'])
        images = body['images']

        for i in range(len(images) - 1):
            assert images[i]['uploaded_at'] >= images[i + 1]['uploaded_at']

    
    def test_list_images_no_query_parameters(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test listing images with no query parameters."""
        db = get_db()

        record = ImageRecord.create(
            user_id='user123',
            filename='photo.png',
            content_type='image/png',
            size_bytes=1024
        )
        db.put_image(record)

        event = {}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['count'] == 1
