from rest_framework.views import exception_handler
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from .response import APIResponse


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response:
        if isinstance(response.data, dict):
            message = response.data.get("detail", "An error occurred!")
        else:
            message = "An error occurred!"

        return APIResponse.error(
            errors=response.data if response.data else str(exc),
            message=message,
            status=response.status_code,
        )

    return APIResponse.error(
        errors=str(exc),
        message="An unexpected error occurred!",
        status=HTTP_500_INTERNAL_SERVER_ERROR,
    )
