"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class UploadImageRequest(BaseModel):
    """Upload image request"""
    user_id: str = Field(..., min_length=1, description="User ID")
    filename: str = Field(..., min_length=1, description="Image filename")
    content_type: str = Field(..., description="Image MIME type (image/jpeg, image/png, image/gif, image/webp)")
    data: str = Field(..., description="Base64-encoded image data")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags")
    caption: Optional[str] = Field(default=None, description="Optional image caption")

    class Config:
        example = {
            "user_id": "user123",
            "filename": "vacation.png",
            "content_type": "image/png",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJg",
            "tags": ["beach", "summer"],
            "caption": "Beautiful sunset"
        }

class ImageResponse(BaseModel):
    """Image response model"""
    image_id: str
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: str
    tags: List[str]
    caption: Optional[str]
    status: str

    class Config:
        example = {
            "image_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user123",
            "filename": "vacation.png",
            "content_type": "image/png",
            "size_bytes": 66,
            "uploaded_at": "2026-05-15T10:30:00Z",
            "tags": ["beach", "summer"],
            "caption": "Beautiful sunset",
            "status": "active"
        }

class UploadImageResponse(BaseModel):
    """Upload response - same as ImageResponse"""
    image_id: str
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: str
    tags: List[str]
    caption: Optional[str]
    status: str

class ListImagesResponse(BaseModel):
    """List images response"""
    count: int
    images: List[ImageResponse]
    next_page_token: Optional[str] = None

    class Config:
        example = {
            "count": 2,
            "images": [
                {
                    "image_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user123",
                    "filename": "vacation.png",
                    "content_type": "image/png",
                    "size_bytes": 66,
                    "uploaded_at": "2026-05-15T10:30:00Z",
                    "tags": ["beach", "summer"],
                    "caption": "Beautiful sunset",
                    "status": "active"
                }
            ],
            "next_page_token": "eyJpbWFnZV9pZCI6IjU1MGU4NDAw..."
        }

class GetImageResponse(BaseModel):
    """Get image response with download URL"""
    image_id: str
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: str
    tags: List[str]
    caption: Optional[str]
    status: str
    download_url: str

    class Config:
        example = {
            "image_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user123",
            "filename": "vacation.png",
            "content_type": "image/png",
            "size_bytes": 66,
            "uploaded_at": "2026-05-15T10:30:00Z",
            "tags": ["beach", "summer"],
            "caption": "Beautiful sunset",
            "status": "active",
            "download_url": "https://instagram-images.s3.amazonaws.com/..."
        }

class DeleteImageResponse(BaseModel):
    """Delete image response"""
    message: str
    image_id: str

    class Config:
        example = {
            "message": "Image deleted successfully",
            "image_id": "550e8400-e29b-41d4-a716-446655440000"
        }

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    status_code: int

    class Config:
        example = {
            "error": "Invalid base64 data",
            "status_code": 400
        }
