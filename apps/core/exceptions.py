"""Domain exceptions with stable machine-readable codes."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for expected domain failures."""

    code = "domain_error"
    http_status = 400
    default_message = "Domain error"

    def __init__(self, message: str | None = None, *, details: dict | None = None):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)

    def as_dict(self) -> dict:
        """Return the API error envelope payload."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class PermissionDenied(DomainError):
    """The current user may not perform the requested action."""

    code = "permission_denied"
    http_status = 403
    default_message = "Permission denied"


class PageNotFound(DomainError):
    """The requested page or title does not resolve to a page."""

    code = "page_not_found"
    http_status = 404
    default_message = "Page not found"


class RevisionNotFound(DomainError):
    """The requested revision does not exist."""

    code = "revision_not_found"
    http_status = 404
    default_message = "Revision not found"


class EditConflict(DomainError):
    """The edit was based on an outdated revision."""

    code = "edit_conflict"
    http_status = 409
    default_message = "The page changed since base_revid"


class TitleConflict(DomainError):
    """A desired title is already active on another page."""

    code = "title_conflict"
    http_status = 409
    default_message = "Title is already in use"


class InvalidTitle(DomainError):
    """A title failed normalization or validation."""

    code = "invalid_title"
    http_status = 400
    default_message = "Invalid title"


class InvalidRevisionSlug(DomainError):
    """A revision lookup value is not a number or a valid slug."""

    code = "invalid_revision_slug"
    http_status = 400
    default_message = "Invalid revision slug"


class ContentValidationError(DomainError):
    """Content or properties failed validation."""

    code = "invalid_content"
    http_status = 400
    default_message = "Invalid content"


class RevisionStateError(DomainError):
    """A revision is missing a required slot."""

    code = "invalid_revision_state"
    http_status = 500
    default_message = "Revision does not have the required slots"


class ContentHashCollision(DomainError):
    """Two different contents produced the same hash."""

    code = "content_hash_collision"
    http_status = 500
    default_message = "Content hash collision"


class RedirectLoop(DomainError):
    """A redirect chain is cyclic or too long."""

    code = "redirect_loop"
    http_status = 409
    default_message = "Redirect loop"
