class BadRequestException(Exception):
    """Raised when the request is invalid or missing required data."""
    pass


class ConflictException(Exception):
    """Raised when a resource already exists (e.g., duplicate phone number)."""
    pass


class UnauthorizedException(Exception):
    """Raised when authentication fails."""
    pass


class NotFoundException(Exception):
    """Raised when a resource is not found."""
    pass


class ExternalServiceException(Exception):
    """Raised when an external service (e.g., SMS) fails."""
    pass