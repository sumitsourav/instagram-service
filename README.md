# Instagram Image Service

A scalable, serverless image upload and storage service built with AWS Lambda, S3, DynamoDB, and API Gateway. Built on Python 3.7+ for efficient image metadata management and cloud storage.

## Features

✅ **Image Upload** - Upload images with metadata, tags, and captions  
✅ **List Images** - Query images with flexible filtering and pagination  
✅ **View/Download** - Retrieve image metadata and presigned download URLs  
✅ **Delete Images** - Soft-delete with metadata preservation  
✅ **Multi-User Support** - Isolated storage per user  
✅ **Scalable Architecture** - Auto-scaling Lambda functions  
✅ **Comprehensive Tests** - 50+ unit tests with moto mocks  
✅ **LocalStack Development** - Local AWS emulation for development  

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.7+
- pip (Python package manager)

### 1. Clone and Setup

```bash
# Navigate to project directory
cd instagram-service

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Start LocalStack

```bash
# Start all AWS services locally
docker-compose up -d

# Verify services are running
docker-compose logs -f localstack
```

LocalStack will automatically create:
- S3 bucket: `instagram-images`
- DynamoDB table: `images` with Global Secondary Indexes
- Required indexes for efficient queries

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=lambdas --cov-report=html

# Run specific test file
pytest tests/test_upload_handler.py -v
```

### 4. Stop Services

```bash
docker-compose down
```

## Project Structure

```
instagram-service/
├── lambdas/
│   ├── shared/              # Shared utilities
│   │   ├── models.py        # ImageRecord data model
│   │   ├── db.py            # DynamoDB operations
│   │   ├── storage.py       # S3 operations
│   │   ├── validators.py    # Input validation
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── __init__.py      # Module exports
│   ├── upload_image/
│   │   └── handler.py       # Upload Lambda function
│   ├── list_images/
│   │   └── handler.py       # List Lambda function
│   ├── get_image/
│   │   └── handler.py       # Get/Download Lambda function
│   └── delete_image/
│       └── handler.py       # Delete Lambda function
├── tests/                   # Unit tests
│   ├── conftest.py          # Pytest fixtures and mocks
│   ├── test_models.py       # Model tests
│   ├── test_validators.py   # Validator tests
│   ├── test_upload_handler.py
│   ├── test_list_handler.py
│   ├── test_get_handler.py
│   ├── test_delete_handler.py
│   └── __init__.py
├── infrastructure/
│   └── init-localstack.sh   # LocalStack initialization script
├── docker-compose.yml       # LocalStack configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── API_DOCUMENTATION.md     # Complete API reference
└── README.md                # This file
```

## API Quick Reference

### Upload Image
```bash
curl -X POST http://localhost:4566/images/upload \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### List Images
```bash
# List all
curl "http://localhost:4566/images"

# By user
curl "http://localhost:4566/images?user_id=user123"

# By content type
curl "http://localhost:4566/images?content_type=image/jpeg"

# With pagination
curl "http://localhost:4566/images?limit=10"
```

### Get Image
```bash
curl "http://localhost:4566/images/{image_id}"
```

### Delete Image
```bash
curl -X DELETE "http://localhost:4566/images/{image_id}"
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete endpoint specifications and examples.

## Development Workflow

### 1. Local Testing

All changes are tested locally using moto (AWS service mocks):

```bash
# Run tests after making changes
pytest tests/ -v

# Watch for changes (requires pytest-watch)
ptw tests/
```

### 2. Code Structure

- **Lambda Handlers** - Each Lambda function in `lambdas/{function_name}/handler.py`
- **Shared Utilities** - Common code in `lambdas/shared/`
- **Database Layer** - `lambdas/shared/db.py` for DynamoDB
- **Storage Layer** - `lambdas/shared/storage.py` for S3

### 3. Adding Features

Example: Adding a new Lambda function

1. Create directory: `lambdas/new_function/`
2. Create handler: `lambdas/new_function/handler.py`
3. Use shared utilities from `lambdas/shared/`
4. Add tests in `tests/test_new_handler.py`
5. Run tests: `pytest tests/test_new_handler.py -v`

## Configuration

### Environment Variables

Configured in Lambda environment (or set locally for testing):

```
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localstack:4566  # For LocalStack
S3_BUCKET_NAME=instagram-images
DYNAMODB_TABLE_NAME=images
PRESIGNED_URL_EXPIRY=3600
```

### LocalStack Configuration

Configured in `docker-compose.yml`:
- **Services**: S3, DynamoDB, Lambda, API Gateway
- **Data persistence**: Optional (stored in `/tmp/localstack/data`)
- **Health checks**: Automatic service validation

### DynamoDB Schema

**Table**: `images`

**Primary Key**: `image_id` (UUID)

**Global Secondary Indexes**:
1. `user_id-uploaded_at-index` - Query by user, sort by date
2. `status-uploaded_at-index` - Query by status, sort by date
3. `content_type-uploaded_at-index` - Query by file type, sort by date

## Test Coverage

```
Test Categories:
├── Models (test_models.py)
│   └── ImageRecord serialization/deserialization
├── Validators (test_validators.py)
│   └── Content type, Base64, ISO dates, UUIDs
├── Upload (test_upload_handler.py)
│   ├── Success cases
│   ├── Validation errors
│   ├── Content type validation
│   └── Base64 encoding
├── List (test_list_handler.py)
│   ├── Filtering (user, content_type, tags, dates)
│   ├── Pagination
│   ├── Sorting (newest first)
│   └── Deleted image exclusion
├── Get (test_get_handler.py)
│   ├── Metadata retrieval
│   ├── Presigned URL generation
│   └── Deleted image handling
└── Delete (test_delete_handler.py)
    ├── Soft delete
    ├── Metadata preservation
    └── S3 removal
```

Run tests with coverage:
```bash
pytest tests/ --cov=lambdas --cov-report=html
open htmlcov/index.html
```

## Data Models

### ImageRecord

Represents an image in the system:

```python
@dataclass
class ImageRecord:
    image_id: str              # UUID
    user_id: str              # User identifier
    s3_key: str               # S3 object path
    filename: str             # Original filename
    content_type: str         # MIME type
    size_bytes: int           # File size
    uploaded_at: str          # ISO-8601 timestamp
    status: str               # "active" or "deleted"
    tags: Set[str]            # Classification tags
    caption: Optional[str]    # Description
```

## Scalability

The service is built for scalability:

1. **Serverless Compute** - Lambda auto-scales to handle traffic spikes
2. **DynamoDB** - On-demand pricing scales with workload
3. **S3** - Unlimited scalable object storage
4. **Global Secondary Indexes** - Efficient queries across multiple dimensions
5. **Pagination** - Handles large result sets efficiently
6. **Presigned URLs** - Direct downloads from S3 without Lambda overhead

## Performance Considerations

- **Payload Size**: API Gateway has a 10 MB limit; base64 encoding increases size by ~33%
- **Database Queries**: GSIs enable sub-second queries even with millions of records
- **Cold Starts**: Consider provisioned concurrency for consistent latency
- **S3 Throughput**: Partitions and parallelization for bulk operations

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Description of the error"
}
```

**Common HTTP Status Codes**:
- `200` - Success
- `201` - Created (upload success)
- `204` - No Content (delete success)
- `400` - Bad Request (validation error)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Troubleshooting

### LocalStack Issues

```bash
# Check logs
docker-compose logs -f localstack

# Restart services
docker-compose down
docker-compose up -d

# Force recreate
docker-compose down --volumes
docker-compose up -d
```

### Test Failures

```bash
# Verbose output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific test
pytest tests/test_models.py::TestImageRecord::test_create_basic -v
```

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.7+

# Use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Dependencies

### Production (`requirements.txt`)
- `boto3>=1.26.0` - AWS SDK
- `python-dateutil>=2.8.2` - Date utilities

### Development (`requirements-dev.txt`)
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `moto>=4.0.0` - AWS service mocking
- `pydantic>=1.10.0` - Data validation

## Contributing

1. Write tests for new features
2. Ensure all tests pass: `pytest tests/ -v`
3. Maintain >80% code coverage
4. Follow existing code patterns
5. Update API_DOCUMENTATION.md for API changes

## AWS Deployment

To deploy to AWS:

1. **Prepare Lambda packages**:
   ```bash
   ./scripts/build-lambda.sh
   ```

2. **Deploy with CloudFormation or Terraform**:
   - Configure API Gateway routes
   - Set environment variables
   - Configure IAM permissions
   - Create S3 bucket and DynamoDB table

3. **Enable VPC (optional)**:
   - For added security
   - Requires VPC endpoints for S3/DynamoDB

4. **Monitor**:
   - CloudWatch logs
   - X-Ray tracing
   - CloudWatch metrics

## License

This project is provided as-is for educational and development purposes.

## Next Steps

1. **Read the API docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Run the tests**: `pytest tests/ -v`
3. **Try the examples**: See API_DOCUMENTATION.md examples section
4. **Deploy to AWS**: Use provided scripts and CloudFormation templates

## Support

For issues or questions:
1. Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. Review test cases for usage examples
3. Check LocalStack logs: `docker-compose logs localstack`
4. Verify environment setup: `docker-compose ps`
