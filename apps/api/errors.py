"""DRF exception handler using the project's error envelope."""

from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.exceptions import DomainError


def api_exception_handler(exc, context):
    """Translate domain and DRF errors into ``{"error": ...}`` responses."""
    if isinstance(exc, DomainError):
        return Response({"error": exc.as_dict()}, status=exc.http_status)

    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(response.data, dict) and "detail" in response.data:
        code = getattr(exc, "default_code", "error")
        message = str(response.data["detail"])
        details = {}
    else:
        code = "validation_error"
        message = "Validation failed"
        details = response.data

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    return response
