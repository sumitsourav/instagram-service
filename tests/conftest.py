import pytest
import os
import json
import base64
from moto import mock_aws
import boto3
from datetime import datetime


@pytest.fixture
def aws_credentials():
    """Set up AWS credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(autouse=True)
def mock_aws_services(aws_credentials):
    """Auto-apply mock_aws to all tests."""
    with mock_aws():
        yield


@pytest.fixture
def s3_bucket(aws_credentials):
    """Create a mocked S3 bucket."""
    client = boto3.client('s3', region_name='us-east-1')
    client.create_bucket(Bucket='instagram-images')
    yield client


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mocked DynamoDB table."""
    client = boto3.client('dynamodb', region_name='us-east-1')

    client.create_table(
        TableName='images',
        KeySchema=[
            {'AttributeName': 'image_id', 'KeyType': 'HASH'},
        ],
        AttributeDefinitions=[
            {'AttributeName': 'image_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'content_type', 'AttributeType': 'S'},
            {'AttributeName': 'uploaded_at', 'AttributeType': 'S'},
        ],
        BillingMode='PAY_PER_REQUEST',
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'user_id-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'status-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'content_type-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'content_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'},
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
    )

    yield client


@pytest.fixture
def aws_env(aws_credentials):
    """Set up environment variables for AWS."""
    os.environ['DYNAMODB_TABLE_NAME'] = 'images'
    os.environ['S3_BUCKET_NAME'] = 'instagram-images'
    os.environ['AWS_ENDPOINT_URL'] = ''
    yield
    for key in ['DYNAMODB_TABLE_NAME', 'S3_BUCKET_NAME', 'AWS_ENDPOINT_URL']:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes."""
    return b'\x89PNG\r\n\x1a\n' + b'x' * 1000


@pytest.fixture
def sample_image_b64(sample_image_bytes):
    """Create sample image as base64."""
    return base64.b64encode(sample_image_bytes).decode('utf-8')


@pytest.fixture
def sample_upload_event(sample_image_b64):
    """Create a sample upload event."""
    return {
        'body': json.dumps({
            'user_id': 'user123',
            'filename': 'photo.png',
            'content_type': 'image/png',
            'data': sample_image_b64,
            'tags': ['nature', 'landscape'],
            'caption': 'Beautiful view'
        })
    }


@pytest.fixture
def sample_list_event():
    """Create a sample list event."""
    return {
        'queryStringParameters': {
            'user_id': 'user123',
            'limit': '10'
        }
    }
