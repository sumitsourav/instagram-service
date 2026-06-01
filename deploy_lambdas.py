#!/usr/bin/env python3
"""
Deploy Lambda functions to LocalStack
"""
import boto3
import zipfile
import os
import io
import sys
import shutil

# Configure boto3 for LocalStack
lambda_client = boto3.client(
    'lambda',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def create_lambda_zip(handler_path):
    """Create a zip file with Lambda handler and dependencies"""
    zip_buffer = io.BytesIO()

    # Get absolute paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    abs_handler_path = os.path.join(project_root, handler_path)
    shared_path = os.path.join(project_root, 'lambdas', 'shared')

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add handler.py
        with open(os.path.join(abs_handler_path, 'handler.py'), 'r') as f:
            zip_file.writestr('handler.py', f.read())

        # Add shared utilities
        for filename in os.listdir(shared_path):
            if filename.endswith('.py'):
                with open(os.path.join(shared_path, filename), 'r') as f:
                    zip_file.writestr(f'lambdas/shared/{filename}', f.read())

    zip_buffer.seek(0)
    return zip_buffer.read()

print("\n" + "=" * 70)
print("🚀 Deploying Lambda Functions to LocalStack")
print("=" * 70)

# Lambda functions to deploy
functions = [
    ('upload-image', 'lambdas/upload_image'),
    ('list-images', 'lambdas/list_images'),
    ('get-image', 'lambdas/get_image'),
    ('delete-image', 'lambdas/delete_image'),
]

try:
    for func_name, handler_path in functions:
        print(f"\nDeploying {func_name}...")

        # Check if function already exists
        try:
            lambda_client.get_function(FunctionName=func_name)
            print(f"  Function already exists, updating...")

            # Create zip
            zip_code = create_lambda_zip(handler_path)

            # Update function code
            lambda_client.update_function_code(
                FunctionName=func_name,
                ZipFile=zip_code
            )
            print(f"  ✅ {func_name} updated")

        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"  Function doesn't exist, creating...")

            # Create zip
            zip_code = create_lambda_zip(handler_path)

            # Create function
            response = lambda_client.create_function(
                FunctionName=func_name,
                Runtime='python3.9',
                Role='arn:aws:iam::000000000000:role/lambda-role',
                Handler='handler.lambda_handler',
                Code={'ZipFile': zip_code},
                Timeout=30,
                MemorySize=256,
                Environment={
                    'Variables': {
                        'DYNAMODB_TABLE_NAME': 'images',
                        'S3_BUCKET_NAME': 'images',
                        'AWS_ENDPOINT_URL': 'http://localhost:4566',
                        'AWS_DEFAULT_REGION': 'us-east-1'
                    }
                }
            )
            print(f"  ✅ {func_name} created: {response['FunctionArn']}")

    print("\n" + "=" * 70)
    print("✅ All Lambda Functions Deployed!")
    print("=" * 70)
    print("\nNext: Run setup_api_gateway.py to configure API Gateway routes")
    print("=" * 70 + "\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
