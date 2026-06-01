import json
import sys
import os
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import (
    get_db,
    parse_iso_date,
    ValidationError, DatabaseError
)


def lambda_handler(event, context):
    """Handle list images with filters."""
    try:
        params = event.get('queryStringParameters') or {}

        user_id = params.get('user_id')
        tag = params.get('tag')
        content_type = params.get('content_type')
        date_from_str = params.get('date_from')
        date_to_str = params.get('date_to')
        last_evaluated_key_b64 = params.get('last_evaluated_key')

        try:
            limit = int(params.get('limit', 50))
            if limit < 1 or limit > 100:
                raise ValueError("limit must be between 1 and 100")
        except ValueError as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

        date_from = None
        date_to = None

        try:
            if date_from_str:
                date_from = parse_iso_date(date_from_str)
                date_from = date_from.isoformat() + 'Z' if date_from else None
            if date_to_str:
                date_to = parse_iso_date(date_to_str)
                date_to = date_to.isoformat() + 'Z' if date_to else None
        except ValidationError as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(e)}),
                'headers': {'Content-Type': 'application/json'}
            }

        start_key = None
        if last_evaluated_key_b64:
            try:
                start_key_json = base64.b64decode(last_evaluated_key_b64).decode('utf-8')
                start_key = json.loads(start_key_json)
            except Exception as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Invalid pagination token: {str(e)}'}),
                    'headers': {'Content-Type': 'application/json'}
                }

        db = get_db()

        if user_id:
            images, next_key = db.query_by_user(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to,
                tag=tag,
                limit=limit,
                start_key=start_key
            )
        elif content_type:
            images, next_key = db.query_by_content_type(
                content_type=content_type,
                date_from=date_from,
                date_to=date_to,
                tag=tag,
                limit=limit,
                start_key=start_key
            )
        else:
            images, next_key = db.query_all_active(
                date_from=date_from,
                date_to=date_to,
                tag=tag,
                limit=limit,
                start_key=start_key
            )

        response_data = {
            'images': [img.to_json() for img in images],
            'count': len(images)
        }

        if next_key:
            next_key_json = json.dumps(next_key)
            next_key_b64 = base64.b64encode(next_key_json.encode('utf-8')).decode('utf-8')
            response_data['next_page_token'] = next_key_b64

        return {
            'statusCode': 200,
            'body': json.dumps(response_data),
            'headers': {'Content-Type': 'application/json'}
        }

    except DatabaseError as e:
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
