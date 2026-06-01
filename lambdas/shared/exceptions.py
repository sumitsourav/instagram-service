class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class NotFoundError(Exception):
    """Raised when a resource is not found."""
    pass


class StorageError(Exception):
    """Raised when S3 operations fail."""
    pass


class DatabaseError(Exception):
    """Raised when DynamoDB operations fail."""
    pass
