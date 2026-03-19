# utils/responses.py
from rest_framework.response import Response
from rest_framework import status


class StandardResponse:
    """Standardized API response utility"""
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """
        Success response format
        {
            "status": "success",
            "message": "Optional success message",
            "data": {...}
        }
        """
        response_data = {"status": "success"}
        
        if message:
            response_data["message"] = message
        
        if data is not None:
            response_data["data"] = data
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Error response format
        {
            "status": "error",
            "message": "Error message"
        }
        """
        response_data = {
            "status": "error",
            "message": message
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(data=None, message="Resource created successfully"):
        """Created response (201)"""
        return StandardResponse.success(data, message, status.HTTP_201_CREATED)
    
    @staticmethod
    def no_content(message="Resource deleted successfully"):
        """No content response (204)"""
        return Response(
            {"status": "success", "message": message},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @staticmethod
    def unauthorized(message="Authentication required"):
        """Unauthorized response (401)"""
        return StandardResponse.error(message, status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def forbidden(message="Permission denied"):
        """Forbidden response (403)"""
        return StandardResponse.error(message, status_code=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Not found response (404)"""
        return StandardResponse.error(message, status_code=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def format_validation_errors(errors):
        """
        Convert DRF validation errors to simple string message
        Input: {"email": ["User with this email already exists."]}
        Output: "User with this email already exists."
        """
        if isinstance(errors, dict):
            # Get first error from first field
            for field, messages in errors.items():
                if isinstance(messages, list) and len(messages) > 0:
                    return str(messages[0])
                elif isinstance(messages, str):
                    return messages
                elif isinstance(messages, dict):
                    # Nested errors
                    return StandardResponse.format_validation_errors(messages)
            return "Validation error occurred"
        elif isinstance(errors, list) and len(errors) > 0:
            return str(errors[0])
        elif isinstance(errors, str):
            return errors
        return "An error occurred"
