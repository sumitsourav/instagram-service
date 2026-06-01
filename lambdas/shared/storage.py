import boto3
import os
from botocore.exceptions import ClientError
from .exceptions import StorageError

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'images')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
PRESIGNED_URL_EXPIRY = int(os.environ.get('PRESIGNED_URL_EXPIRY', '3600'))


class S3Storage:
    def __init__(self):
        if AWS_ENDPOINT_URL:
            self.client = boto3.client(
                's3',
                endpoint_url=AWS_ENDPOINT_URL,
                region_name=AWS_REGION,
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'testing'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'testing')
            )
        else:
            self.client = boto3.client('s3', region_name=AWS_REGION)

    def upload_image(self, s3_key, data_bytes, content_type):
        """Upload image bytes to S3."""
        try:
            self.client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=data_bytes,
                ContentType=content_type
            )
        except ClientError as e:
            raise StorageError(f"Failed to upload image to S3: {str(e)}")

    def delete_image(self, s3_key):
        """Delete image from S3."""
        try:
            self.client.delete_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
        except ClientError as e:
            raise StorageError(f"Failed to delete image from S3: {str(e)}")

    def generate_presigned_url(self, s3_key, expires_in=None):
        """Generate a presigned URL for downloading an image."""
        if expires_in is None:
            expires_in = PRESIGNED_URL_EXPIRY

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': S3_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")


def get_storage():
    """Factory function to get S3 storage instance."""
    return S3Storage()
