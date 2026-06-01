import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import (
    get_db, get_storage,
    NotFoundError, DatabaseError, StorageError
)


def lambda_handler(event, context):
    """Handle delete image."""
    try:
        image_id = event.get('pathParameters', {}).get('id')

        if not image_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing image_id'}),
                'headers': {'Content-Type': 'application/json'}
            }

        db = get_db()

        image_record = db.get_image(image_id)

        if image_record.status != 'active':
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Image not found'}),
                'headers': {'Content-Type': 'application/json'}
            }

        storage = get_storage()
        storage.delete_image(image_record.s3_key)

        db.update_image_status(image_id, 'deleted')

        return {
            'statusCode': 204,
            'body': '',
            'headers': {}
        }

    except NotFoundError:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Image not found'}),
            'headers': {'Content-Type': 'application/json'}
        }
    except (DatabaseError, StorageError) as e:
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
