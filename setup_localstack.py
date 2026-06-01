#!/usr/bin/env python3
"""
Setup script for LocalStack resources
"""
import boto3
import json

# Configure boto3 to use LocalStack
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

dynamodb = boto3.client(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

print("Setting up LocalStack resources...")

# 1. Create S3 bucket
print("\n1. Creating S3 bucket...")
try:
    s3.create_bucket(Bucket='images')
    print("   ✓ S3 bucket created")
except s3.exceptions.BucketAlreadyExists:
    print("   ✓ S3 bucket already exists")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 2. Enable CORS
print("\n2. Enabling CORS...")
try:
    cors_config = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['ETag', 'x-amz-version-id'],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    s3.put_bucket_cors(Bucket='images', CORSConfiguration=cors_config)
    print("   ✓ CORS enabled")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 3. Create DynamoDB table
print("\n3. Creating DynamoDB table...")
try:
    dynamodb.create_table(
        TableName='images',
        KeySchema=[
            {'AttributeName': 'image_id', 'KeyType': 'HASH'}
        ],
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
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
            {
                'IndexName': 'status-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'status', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
            {
                'IndexName': 'content_type-uploaded_at-index',
                'KeySchema': [
                    {'AttributeName': 'content_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'uploaded_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    print("   ✓ DynamoDB table created")
except dynamodb.exceptions.ResourceInUseException:
    print("   ✓ DynamoDB table already exists")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. Verify setup
print("\n4. Verifying setup...")
try:
    buckets = s3.list_buckets()
    print(f"   ✓ S3 buckets: {[b['Name'] for b in buckets['Buckets']]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    tables = dynamodb.list_tables()
    print(f"   ✓ DynamoDB tables: {tables['TableNames']}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n✅ Setup complete!")
