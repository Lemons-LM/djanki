"""Domain exceptions for user and block operations."""

from apps.core.exceptions import DomainError


class UserNotFound(DomainError):
    """The requested user does not exist."""

    code = "user_not_found"
    http_status = 404
    default_message = "User not found"


class InvalidBlock(DomainError):
    """A block request is invalid."""

    code = "invalid_block"
    http_status = 400
    default_message = "Invalid block"
