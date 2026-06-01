#!/bin/bash
set -e

echo "Initializing LocalStack resources..."

# Create S3 bucket
echo "Creating S3 bucket..."
awslocal s3 mb s3://images || true

# Enable CORS on bucket
echo "Enabling CORS on S3 bucket..."
cat > /tmp/cors.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-version-id"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF
awslocal s3api put-bucket-cors --bucket images --cors-configuration file:///tmp/cors.json || true

# Create DynamoDB table
echo "Creating DynamoDB table..."
awslocal dynamodb create-table \
  --table-name images \
  --attribute-definitions \
    AttributeName=image_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=status,AttributeType=S \
    AttributeName=content_type,AttributeType=S \
    AttributeName=uploaded_at,AttributeType=S \
  --key-schema \
    AttributeName=image_id,KeyType=HASH \
  --global-secondary-indexes \
    'IndexName=user_id-uploaded_at-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=uploaded_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
    'IndexName=status-uploaded_at-index,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=uploaded_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
    'IndexName=content_type-uploaded_at-index,KeySchema=[{AttributeName=content_type,KeyType=HASH},{AttributeName=uploaded_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}' \
  --billing-mode PAY_PER_REQUEST || true

echo "LocalStack initialization complete!"
