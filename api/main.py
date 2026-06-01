"""
Instagram Image Service - FastAPI Application

This FastAPI application wraps the Lambda handlers and provides
REST API endpoints for image upload, listing, retrieval, and deletion.
"""
import sys
import os
import json
from typing import Optional, List

# Add parent directory to path so we can import lambdas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    UploadImageRequest,
    UploadImageResponse,
    ListImagesResponse,
    GetImageResponse,
    DeleteImageResponse,
    ErrorResponse,
    ImageResponse
)

from lambdas.upload_image.handler import lambda_handler as upload_handler
from lambdas.list_images.handler import lambda_handler as list_handler
from lambdas.get_image.handler import lambda_handler as get_handler
from lambdas.delete_image.handler import lambda_handler as delete_handler
from lambdas.shared.exceptions import ValidationError, NotFoundError, StorageError, DatabaseError

# Set environment variables for LocalStack
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_SECURITY_TOKEN'] = 'test'
os.environ['AWS_SESSION_TOKEN'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_NAME'] = 'images'
os.environ['S3_BUCKET_NAME'] = 'images'
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'

# Create FastAPI app
app = FastAPI(
    title="Instagram Image Service API",
    description="A serverless image storage and management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Health Check =====
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Instagram Image Service API",
        "version": "1.0.0"
    }

# ===== Upload Image =====
@app.post(
    "/images/upload",
    response_model=UploadImageResponse,
    status_code=201,
    tags=["Images"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - validation error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_image(request: UploadImageRequest):
    """
    Upload an image with metadata.

    **Request body:**
    - `user_id`: User identifier
    - `filename`: Original filename
    - `content_type`: MIME type (image/jpeg, image/png, image/gif, image/webp)
    - `data`: Base64-encoded image data
    - `tags`: Optional list of tags
    - `caption`: Optional image caption

    **Returns:**
    - Image details with generated image_id, s3_key, and upload timestamp
    """
    try:
        # Convert Pydantic model to dict for Lambda handler
        body = request.dict()

        # Create Lambda event
        event = {'body': json.dumps(body)}

        # Call Lambda handler
        response = upload_handler(event, None)

        # Check status code
        if response['statusCode'] not in [200, 201]:
            error_body = json.loads(response['body'])
            raise HTTPException(
                status_code=response['statusCode'],
                detail=error_body.get('error', 'Upload failed')
            )

        # Return response
        body = json.loads(response['body'])
        return UploadImageResponse(**body)

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (StorageError, DatabaseError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ===== List Images =====
@app.get(
    "/images",
    response_model=ListImagesResponse,
    status_code=200,
    tags=["Images"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request - invalid parameters"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def list_images(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    content_type: Optional[str] = Query(None, description="Filter by content type (image/jpeg, image/png, etc)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO-8601 format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO-8601 format)"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Results per page (1-100)"),
    last_evaluated_key: Optional[str] = Query(None, description="Pagination token from previous response")
):
    """
    List images with optional filtering and pagination.

    **Query parameters:**
    - `user_id`: Filter images by user
    - `content_type`: Filter by file type (image/jpeg, image/png, image/gif, image/webp)
    - `tag`: Filter by tag (returns images with this tag)
    - `date_from`: Filter images from this date (ISO-8601)
    - `date_to`: Filter images up to this date (ISO-8601)
    - `limit`: Number of results per page (default: 10, max: 100)
    - `last_evaluated_key`: Pagination token from previous response

    **Returns:**
    - List of images matching filters
    - `next_page_token` if more results available
    """
    try:
        # Build query parameters
        query_params = {}
        if user_id:
            query_params['user_id'] = user_id
        if content_type:
            query_params['content_type'] = content_type
        if tag:
            query_params['tag'] = tag
        if date_from:
            query_params['date_from'] = date_from
        if date_to:
            query_params['date_to'] = date_to
        if limit:
            query_params['limit'] = str(limit)
        if last_evaluated_key:
            query_params['last_evaluated_key'] = last_evaluated_key

        # Create Lambda event
        event = {
            'queryStringParameters': query_params if query_params else None
        }

        # Call Lambda handler
        response = list_handler(event, None)

        # Check status code
        if response['statusCode'] != 200:
            error_body = json.loads(response['body'])
            raise HTTPException(
                status_code=response['statusCode'],
                detail=error_body.get('error', 'List failed')
            )

        # Return response
        body = json.loads(response['body'])

        # Convert images to ImageResponse objects
        images = [ImageResponse(**img) for img in body['images']]

        return ListImagesResponse(
            count=body['count'],
            images=images,
            next_page_token=body.get('next_page_token')
        )

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ===== Get Image =====
@app.get(
    "/images/{image_id}",
    response_model=GetImageResponse,
    status_code=200,
    tags=["Images"],
    responses={
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_image(image_id: str):
    """
    Get image details and presigned download URL.

    **Path parameters:**
    - `image_id`: UUID of the image

    **Returns:**
    - Image metadata
    - Presigned S3 URL (valid for 1 hour)
    """
    try:
        # Create Lambda event
        event = {
            'pathParameters': {'image_id': image_id}
        }

        # Call Lambda handler
        response = get_handler(event, None)

        # Check status code
        if response['statusCode'] != 200:
            error_body = json.loads(response['body'])
            if response['statusCode'] == 404:
                raise HTTPException(status_code=404, detail="Image not found")
            raise HTTPException(
                status_code=response['statusCode'],
                detail=error_body.get('error', 'Get failed')
            )

        # Return response
        body = json.loads(response['body'])
        return GetImageResponse(**body)

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (StorageError, DatabaseError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ===== Delete Image =====
@app.delete(
    "/images/{image_id}",
    response_model=DeleteImageResponse,
    status_code=200,
    tags=["Images"],
    responses={
        404: {"model": ErrorResponse, "description": "Image not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def delete_image(image_id: str):
    """
    Delete an image (soft delete - preserves metadata).

    **Path parameters:**
    - `image_id`: UUID of the image

    **Returns:**
    - Confirmation message with deleted image_id

    **Note:** Image is soft-deleted (status marked as 'deleted') to preserve audit trails.
    """
    try:
        # Create Lambda event
        event = {
            'pathParameters': {'image_id': image_id}
        }

        # Call Lambda handler
        response = delete_handler(event, None)

        # Check status code
        if response['statusCode'] != 200:
            error_body = json.loads(response['body'])
            if response['statusCode'] == 404:
                raise HTTPException(status_code=404, detail="Image not found")
            raise HTTPException(
                status_code=response['statusCode'],
                detail=error_body.get('error', 'Delete failed')
            )

        # Return response
        body = json.loads(response['body'])
        return DeleteImageResponse(**body)

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (StorageError, DatabaseError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ===== Exception Handlers =====
@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "status_code": 400}
    )

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request, exc):
    """Handle not found errors"""
    return JSONResponse(
        status_code=404,
        content={"error": str(exc), "status_code": 404}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
