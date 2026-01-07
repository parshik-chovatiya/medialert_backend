
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for standardized error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize error response
        error_data = {
            "status": "error",
            "message": "An error occurred"
        }
        
        # Handle different exception types
        if isinstance(exc, ValidationError):
            error_data["message"] = "Validation error"
            error_data["errors"] = response.data
        elif isinstance(exc, AuthenticationFailed):
            error_data["message"] = str(exc)
        elif isinstance(exc, NotFound):
            error_data["message"] = str(exc)
        else:
            # Generic error message
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    error_data["message"] = response.data['detail']
                else:
                    error_data["message"] = str(response.data)
                    error_data["errors"] = response.data
            else:
                error_data["message"] = str(response.data)
        
        response.data = error_data
    
    return response