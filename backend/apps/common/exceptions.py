"""
A consistent error envelope for the whole API (10.5).

Every handled error becomes:
    {"error": {"status": 400, "code": "validation_error",
               "message": "...", "fields": {...}}}

``fields`` is present only for validation errors. Unhandled (500) errors are left
to Django.
"""
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

_CODES = {
    exceptions.ValidationError: "validation_error",
    exceptions.AuthenticationFailed: "authentication_failed",
    exceptions.NotAuthenticated: "not_authenticated",
    # Django's Http404 / PermissionDenied are converted to responses by DRF but
    # arrive here as the original Django exception, so map them explicitly.
    Http404: "not_found",
    exceptions.NotFound: "not_found",
    DjangoPermissionDenied: "permission_denied",
    exceptions.PermissionDenied: "permission_denied",
    exceptions.MethodNotAllowed: "method_not_allowed",
    exceptions.Throttled: "throttled",
}


def _code_for(exc) -> str:
    for klass, code in _CODES.items():
        if isinstance(exc, klass):
            return code
    return "error"


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # unexpected error -> Django returns 500

    data = response.data
    fields = None
    if isinstance(data, dict) and set(data) == {"detail"}:
        message = str(data["detail"])
    elif isinstance(data, list):
        message = "; ".join(str(x) for x in data)
    else:
        # field-level validation errors
        message = "Validation failed."
        fields = data

    error = {
        "status": response.status_code,
        "code": _code_for(exc),
        "message": message,
    }
    if fields is not None:
        error["fields"] = fields
    response.data = {"error": error}
    return response
