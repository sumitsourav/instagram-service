import boto3
import os
import base64
import json
from datetime import datetime
from botocore.exceptions import ClientError
from .exceptions import DatabaseError, NotFoundError
from .models import ImageRecord

DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'images')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

class DynamoDBStorage:
    def __init__(self):
        if AWS_ENDPOINT_URL:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=AWS_ENDPOINT_URL,
                region_name=AWS_REGION,
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'testing'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'testing')
            )
        else:
            self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

        self.table = self.dynamodb.Table(DYNAMODB_TABLE_NAME)

    def put_image(self, image_record):
        """Store image metadata in DynamoDB."""
        try:
            self.table.put_item(Item=image_record.to_dynamo_item())
        except ClientError as e:
            raise DatabaseError(f"Failed to store image metadata: {str(e)}")

    def get_image(self, image_id):
        """Retrieve image metadata by ID."""
        try:
            response = self.table.get_item(Key={'image_id': image_id})
            if 'Item' not in response:
                raise NotFoundError(f"Image not found: {image_id}")
            return ImageRecord.from_dynamo_item(response['Item'])
        except ClientError as e:
            raise DatabaseError(f"Failed to retrieve image metadata: {str(e)}")

    def update_image_status(self, image_id, status):
        """Update image status (e.g., mark as deleted)."""
        try:
            self.table.update_item(
                Key={'image_id': image_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status}
            )
        except ClientError as e:
            raise DatabaseError(f"Failed to update image status: {str(e)}")

    def query_by_user(self, user_id, date_from=None, date_to=None, tag=None, limit=50, start_key=None):
        """Query images by user_id using GSI."""
        try:
            key_condition = 'user_id = :user_id'
            expression_values = {':user_id': user_id, ':status': 'active'}
            expression_names = {}

            if date_from and date_to:
                key_condition += ' AND uploaded_at BETWEEN :date_from AND :date_to'
                expression_values[':date_from'] = date_from
                expression_values[':date_to'] = date_to
            elif date_from:
                key_condition += ' AND uploaded_at >= :date_from'
                expression_values[':date_from'] = date_from
            elif date_to:
                key_condition += ' AND uploaded_at <= :date_to'
                expression_values[':date_to'] = date_to

            filter_expression = '#status = :status'
            if tag:
                filter_expression += ' AND contains(#tags, :tag)'
                expression_values[':tag'] = tag
                expression_names['#tags'] = 'tags'

            expression_names['#status'] = 'status'

            kwargs = {
                'IndexName': 'user_id-uploaded_at-index',
                'KeyConditionExpression': key_condition,
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_values,
                'ExpressionAttributeNames': expression_names,
                'Limit': limit,
                'ScanIndexForward': False  # Newest first
            }

            if start_key:
                kwargs['ExclusiveStartKey'] = start_key

            response = self.table.query(**kwargs)

            items = [ImageRecord.from_dynamo_item(item) for item in response.get('Items', [])]
            next_key = response.get('LastEvaluatedKey')

            return items, next_key
        except ClientError as e:
            raise DatabaseError(f"Failed to query images by user: {str(e)}")

    def query_by_content_type(self, content_type, date_from=None, date_to=None, tag=None, limit=50, start_key=None):
        """Query images by content_type using GSI."""
        try:
            key_condition = 'content_type = :content_type'
            expression_values = {':content_type': content_type, ':status': 'active'}
            expression_names = {}

            if date_from and date_to:
                key_condition += ' AND uploaded_at BETWEEN :date_from AND :date_to'
                expression_values[':date_from'] = date_from
                expression_values[':date_to'] = date_to
            elif date_from:
                key_condition += ' AND uploaded_at >= :date_from'
                expression_values[':date_from'] = date_from
            elif date_to:
                key_condition += ' AND uploaded_at <= :date_to'
                expression_values[':date_to'] = date_to

            filter_expression = '#status = :status'
            if tag:
                filter_expression += ' AND contains(#tags, :tag)'
                expression_values[':tag'] = tag
                expression_names['#tags'] = 'tags'

            expression_names['#status'] = 'status'

            kwargs = {
                'IndexName': 'content_type-uploaded_at-index',
                'KeyConditionExpression': key_condition,
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_values,
                'ExpressionAttributeNames': expression_names,
                'Limit': limit,
                'ScanIndexForward': False
            }

            if start_key:
                kwargs['ExclusiveStartKey'] = start_key

            response = self.table.query(**kwargs)

            items = [ImageRecord.from_dynamo_item(item) for item in response.get('Items', [])]
            next_key = response.get('LastEvaluatedKey')

            return items, next_key
        except ClientError as e:
            raise DatabaseError(f"Failed to query images by content_type: {str(e)}")

    def query_all_active(self, date_from=None, date_to=None, tag=None, limit=50, start_key=None):
        """Query all active images using GSI, optionally filtered by date range and tag."""
        try:
            key_condition = '#status = :status'
            expression_values = {':status': 'active'}
            expression_names = {'#status': 'status'}

            if date_from and date_to:
                key_condition += ' AND uploaded_at BETWEEN :date_from AND :date_to'
                expression_values[':date_from'] = date_from
                expression_values[':date_to'] = date_to
            elif date_from:
                key_condition += ' AND uploaded_at >= :date_from'
                expression_values[':date_from'] = date_from
            elif date_to:
                key_condition += ' AND uploaded_at <= :date_to'
                expression_values[':date_to'] = date_to

            filter_expression = None
            if tag:
                filter_expression = 'contains(#tags, :tag)'
                expression_values[':tag'] = tag
                expression_names['#tags'] = 'tags'

            kwargs = {
                'IndexName': 'status-uploaded_at-index',
                'KeyConditionExpression': key_condition,
                'ExpressionAttributeValues': expression_values,
                'ExpressionAttributeNames': expression_names,
                'Limit': limit,
                'ScanIndexForward': False
            }

            if filter_expression:
                kwargs['FilterExpression'] = filter_expression

            if start_key:
                kwargs['ExclusiveStartKey'] = start_key

            response = self.table.query(**kwargs)

            items = [ImageRecord.from_dynamo_item(item) for item in response.get('Items', [])]
            next_key = response.get('LastEvaluatedKey')

            return items, next_key
        except ClientError as e:
            raise DatabaseError(f"Failed to query all active images: {str(e)}")


def get_db():
    """Factory function to get DynamoDB storage instance."""
    return DynamoDBStorage()
