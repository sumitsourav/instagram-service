import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import (
    get_db, get_storage,
    NotFoundError, DatabaseError, StorageError
)


def lambda_handler(event, context):
    """Handle get image with download URL."""
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
        download_url = storage.generate_presigned_url(image_record.s3_key)


        # print(f"download_url: {download_url}")
        response_data = image_record.to_json()
        response_data['download_url'] = download_url

        return {
            'statusCode': 200,
            'body': json.dumps(response_data),
            'headers': {'Content-Type': 'application/json'}
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
