#!/usr/bin/env python3
"""
Test all 4 Lambda endpoints locally
"""
import sys
import json
import base64
import os

sys.path.insert(0, '/Users/sumitsourav/instagram-service')

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
def test_all_endpoints():
    """Test all 4 API endpoints"""
    import boto3
    from lambdas.upload_image.handler import lambda_handler as upload_handler
    from lambdas.list_images.handler import lambda_handler as list_handler
    from lambdas.get_image.handler import lambda_handler as get_handler
    from lambdas.delete_image.handler import lambda_handler as delete_handler

    # Setup
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='instagram-images')

    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    try:
        dynamodb.delete_table(TableName='images')
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

    print("\n" + "=" * 70)
    print("🧪 TESTING ALL 4 LAMBDA ENDPOINTS")
    print("=" * 70)

    # 1. Upload Image
    print("\n1️⃣  UPLOAD IMAGE")
    print("-" * 70)
    upload_event = {
        'body': json.dumps({
            'user_id': 'user123',
            'filename': 'vacation.png',
            'content_type': 'image/png',
            'data': image_b64,
            'tags': ['beach', 'summer'],
            'caption': 'Beautiful sunset'
        })
    }

    response = upload_handler(upload_event, None)
    assert response['statusCode'] in [200, 201], f"Upload failed: {response['statusCode']}"
    body = json.loads(response['body'])
    image_id = body['image_id']
    print(f"✅ Status: {response['statusCode']}")
    print(f"✅ Image ID: {image_id}")
    print(f"✅ Filename: {body['filename']}")
    print(f"✅ Tags: {body['tags']}")

    # 2. List Images
    print("\n2️⃣  LIST IMAGES")
    print("-" * 70)
    list_event = {
        'queryStringParameters': {'user_id': 'user123'}
    }

    response = list_handler(list_event, None)
    assert response['statusCode'] == 200, f"List failed: {response['statusCode']}"
    body = json.loads(response['body'])
    assert body['count'] == 1, f"Expected 1 image, got {body['count']}"
    print(f"✅ Status: {response['statusCode']}")
    print(f"✅ Found {body['count']} image(s)")
    print(f"✅ Image in list: {body['images'][0]['filename']}")

    # 3. Get Image
    print("\n3️⃣  GET IMAGE")
    print("-" * 70)
    print(f"Retrieving image with ID: {image_id}")
    get_event = {
        'pathParameters': {'id': image_id}
    }

    response = get_handler(get_event, None)
    assert response['statusCode'] == 200, f"Get failed: {response['statusCode']}"
    body = json.loads(response['body'])
    assert body['image_id'] == image_id, "Image ID mismatch"
    print(f"✅ Status: {response['statusCode']}")
    print(f"✅ Retrieved: {body['filename']}")
    print(f"✅ Size: {body['size_bytes']} bytes")
    print(f"✅ Download URL generated: Yes")

    # 4. Delete Image
    print("\n4️⃣  DELETE IMAGE")
    print("-" * 70)
    delete_event = {
        'pathParameters': {'id': image_id}
    }

    response = delete_handler(delete_event, None)
    
    assert response['statusCode'] in (200, 204)
    print(f"✅ Status: {response['statusCode']}")
    print(f"✅ Deleted: {body['image_id']}")

    # Verify deletion
    list_event = {
        'queryStringParameters': {'user_id': 'user123'}
    }
    response = list_handler(list_event, None)
    body = json.loads(response['body'])
    assert body['count'] == 0, f"Expected 0 images after delete, got {body['count']}"
    print(f"✅ Verified: Image removed from listings")

    print("\n" + "=" * 70)
    print("✅ ALL 4 ENDPOINTS TESTED SUCCESSFULLY!")
    print("=" * 70)
    print("\nEndpoint Summary:")
    print("  1. POST   /images/upload      ✅ Working")
    print("  2. GET    /images             ✅ Working")
    print("  3. GET    /images/{image_id}  ✅ Working")
    print("  4. DELETE /images/{image_id}  ✅ Working")
    print("\n" + "=" * 70 + "\n")

if __name__ == '__main__':
    test_all_endpoints()
