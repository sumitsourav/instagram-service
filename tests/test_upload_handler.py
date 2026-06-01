import pytest
import json
import base64
import os
from moto import mock_aws
from lambdas.upload_image.handler import lambda_handler


class TestUploadImageHandler:
    def test_upload_image_success(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test successful image upload."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'content_type': 'image/png',
                'data': sample_image_b64,
                'tags': ['nature', 'landscape'],
                'caption': 'Beautiful sunset'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['user_id'] == 'user123'
        assert body['filename'] == 'photo.png'
        assert body['content_type'] == 'image/png'
        assert body['status'] == 'active'
        assert set(body['tags']) == {'nature', 'landscape'}
        assert body['caption'] == 'Beautiful sunset'
        assert 'image_id' in body
        assert 's3_key' in body
        assert 'uploaded_at' in body

    
    def test_upload_image_without_optional_fields(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test image upload without optional fields."""
        event = {
            'body': json.dumps({
                'user_id': 'user456',
                'filename': 'photo.jpg',
                'content_type': 'image/jpeg',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['user_id'] == 'user456'
        assert body['tags'] == []
        assert 'caption' not in body

    
    def test_upload_image_missing_user_id(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test upload without user_id."""
        event = {
            'body': json.dumps({
                'filename': 'photo.png',
                'content_type': 'image/png',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_id' in body['error']

    
    def test_upload_image_missing_filename(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test upload without filename."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'content_type': 'image/png',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'filename' in body['error']

    
    def test_upload_image_missing_content_type(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test upload without content_type."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'content_type' in body['error']

    
    def test_upload_image_missing_data(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test upload without image data."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'content_type': 'image/png'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'data' in body['error']

    
    def test_upload_image_invalid_content_type(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test upload with unsupported content type."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'document.pdf',
                'content_type': 'application/pdf',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Unsupported content_type' in body['error']

    
    def test_upload_image_invalid_base64(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test upload with invalid base64 data."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'content_type': 'image/png',
                'data': 'not-valid-base64!!!'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid base64 data' in body['error']

    
    def test_upload_image_empty_body(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test upload with empty body."""
        event = {'body': '{}'}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    
    def test_upload_image_no_body(self, aws_credentials, s3_bucket, dynamodb_table, aws_env):
        """Test upload with no body."""
        event = {}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400

    
    def test_upload_image_multiple_tags(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test upload with multiple tags."""
        tags = ['nature', 'landscape', 'sunset', 'mountains']
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'content_type': 'image/png',
                'data': sample_image_b64,
                'tags': tags
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert set(body['tags']) == set(tags)

    
    def test_upload_image_jpeg(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test uploading JPEG image."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.jpg',
                'content_type': 'image/jpeg',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['content_type'] == 'image/jpeg'

    
    def test_upload_image_gif(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test uploading GIF image."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'animation.gif',
                'content_type': 'image/gif',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['content_type'] == 'image/gif'

    
    def test_upload_image_webp(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test uploading WebP image."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.webp',
                'content_type': 'image/webp',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['content_type'] == 'image/webp'

    
    def test_upload_image_response_headers(self, aws_credentials, s3_bucket, dynamodb_table, aws_env, sample_image_b64):
        """Test that upload response has correct headers."""
        event = {
            'body': json.dumps({
                'user_id': 'user123',
                'filename': 'photo.png',
                'content_type': 'image/png',
                'data': sample_image_b64
            })
        }

        response = lambda_handler(event, None)

        assert response['headers']['Content-Type'] == 'application/json'
