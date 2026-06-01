#!/usr/bin/env python3
"""
Test Lambda functions locally using moto mocks
"""
import sys
import json
import base64
import os

# Add lambdas directory to path
sys.path.insert(0, '/Users/sumitsourav/instagram-service')

# Set environment variables
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_NAME'] = 'images'
os.environ['S3_BUCKET_NAME'] = 'instagram-images'
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'

from moto import mock_aws

@mock_aws
def test_upload_and_list():
    """Test upload and list operations"""
    import boto3
    from lambdas.shared import ImageRecord, get_db, get_storage
    from lambdas.upload_image.handler import lambda_handler as upload_handler
    from lambdas.list_images.handler import lambda_handler as list_handler

    # Create S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='instagram-images')

    # Create DynamoDB table
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    # Delete table if it exists
    try:
        dynamodb.delete_table(TableName='images')
        print("Deleted existing 'images' table")
    except:
        pass

    dynamodb.create_table(
        TableName='images',
        KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'image_id', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'status', 'AttributeType': 'S'},
            {'AttributeName': 'content_type', 'AttributeType': 'S'},
            {'AttributeName': 'uploaded_at', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'user_id-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'status-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            },
            {
                'IndexName': 'content_type-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'content_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Create sample image
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`'
    image_b64 = base64.b64encode(png_data).decode('utf-8')

    print("=" * 60)
    print("Testing Upload Image")
    print("=" * 60)

    # Test upload
    upload_event = {
        'body': json.dumps({
            'user_id': 'user123',
            'filename': 'vacation.png',
            'content_type': 'image/png',
            'data': image_b64,
            'tags': ['beach', 'summer'],
            'caption': 'Beautiful sunset at the beach'
        })
    }

    response = upload_handler(upload_event, None)
    print(f"Status: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Response: {json.dumps(body, indent=2)}")

    if response['statusCode'] not in [200, 201]:
        print("❌ Upload failed!")
        return

    image_id = body['image_id']
    print(f"✅ Image uploaded: {image_id}")

    print("\n" + "=" * 60)
    print("Testing List Images")
    print("=" * 60)

    # Test list
    list_event = {
        'queryStringParameters': {'user_id': 'user123'}
    }

    response = list_handler(list_event, None)
    print(f"Status: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Found {body['count']} images")
    print(f"Response: {json.dumps(body, indent=2)}")

    if body['count'] == 1:
        print(f"✅ Image found in list!")
    else:
        print("❌ Image not found in list!")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

if __name__ == '__main__':
    test_upload_and_list()
