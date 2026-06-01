from dataclasses import dataclass, asdict, field
from typing import Optional, Set
from datetime import datetime
import uuid
import json


@dataclass
class ImageRecord:
    image_id: str
    user_id: str
    s3_key: str
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: str
    status: str = "active"
    tags: Set[str] = field(default_factory=set)
    caption: Optional[str] = None

    @classmethod
    def create(cls, user_id, filename, content_type, size_bytes, tags=None, caption=None):
        """Create a new ImageRecord with generated IDs and timestamps."""
        image_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        s3_key = f"users/{user_id}/{image_id}/{filename}"

        return cls(
            image_id=image_id,
            user_id=user_id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            uploaded_at=now,
            tags=set(tags) if tags else set(),
            caption=caption
        )

    def to_dynamo_item(self):
        """Convert to DynamoDB item format (preserving types for boto3)."""
        item = {
            'image_id': self.image_id,
            'user_id': self.user_id,
            's3_key': self.s3_key,
            'filename': self.filename,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
            'uploaded_at': self.uploaded_at,
            'status': self.status,
        }

        if self.caption:
            item['caption'] = self.caption

        if self.tags:
            item['tags'] = self.tags

        return item

    @classmethod
    def from_dynamo_item(cls, item):
        """Convert DynamoDB item to ImageRecord."""
        return cls(
            image_id=item['image_id'],
            user_id=item['user_id'],
            s3_key=item['s3_key'],
            filename=item['filename'],
            content_type=item['content_type'],
            size_bytes=item['size_bytes'],
            uploaded_at=item['uploaded_at'],
            status=item.get('status', 'active'),
            tags=set(item.get('tags', [])),
            caption=item.get('caption')
        )

    def to_json(self):
        """Convert to JSON-serializable dict."""
        from decimal import Decimal

        size_bytes = self.size_bytes
        if isinstance(size_bytes, Decimal):
            size_bytes = int(size_bytes)

        data = {
            'image_id': self.image_id,
            'user_id': self.user_id,
            's3_key': self.s3_key,
            'filename': self.filename,
            'content_type': self.content_type,
            'size_bytes': size_bytes,
            'uploaded_at': self.uploaded_at,
            'status': self.status,
        }

        if self.caption:
            data['caption'] = self.caption

        if self.tags:
            data['tags'] = sorted(list(self.tags))
        else:
            data['tags'] = []

        return data
