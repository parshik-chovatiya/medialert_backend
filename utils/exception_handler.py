# utils/exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound, PermissionDenied
from rest_framework import status as http_status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for standardized error responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_message = "An error occurred"
        
        # Handle different exception types
        if isinstance(exc, ValidationError):
            from utils.responses import StandardResponse
            error_message = StandardResponse.format_validation_errors(response.data)
        elif isinstance(exc, AuthenticationFailed):
            error_message = str(exc)
        elif isinstance(exc, PermissionDenied):
            error_message = str(exc)
        elif isinstance(exc, NotFound):
            error_message = str(exc)
        else:
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    error_message = str(response.data['detail'])
                else:
                    from utils.responses import StandardResponse
                    error_message = StandardResponse.format_validation_errors(response.data)
            elif isinstance(response.data, list):
                error_message = str(response.data[0]) if response.data else "An error occurred"
            else:
                error_message = str(response.data)
        
        # Return standardized error response
        response.data = {
            "status": "error",
            "message": error_message
        }
    
    return response
