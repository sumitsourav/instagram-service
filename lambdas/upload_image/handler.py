import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import (
    get_db, get_storage, ImageRecord,
    validate_content_type, validate_base64, validate_required_field,
    ValidationError, StorageError, DatabaseError
)


def lambda_handler(event, context):
    """Handle image upload."""
    try:
        body = json.loads(event.get('body', '{}'))

        user_id = validate_required_field(body, 'user_id')
        filename = validate_required_field(body, 'filename')
        content_type = validate_required_field(body, 'content_type')
        data_b64 = validate_required_field(body, 'data')

        validate_content_type(content_type)
        image_bytes = validate_base64(data_b64)

        tags = body.get('tags', [])
        caption = body.get('caption')

        image_record = ImageRecord.create(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(image_bytes),
            tags=tags,
            caption=caption
        )

        storage = get_storage()
        storage.upload_image(image_record.s3_key, image_bytes, content_type)

        db = get_db()
        db.put_image(image_record)

        return {
            'statusCode': 201,
            'body': json.dumps(image_record.to_json()),
            'headers': {'Content-Type': 'application/json'}
        }

    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
    except (StorageError, DatabaseError) as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Unexpected error: {str(e)}'}),
            'headers': {'Content-Type': 'application/json'}
        }
