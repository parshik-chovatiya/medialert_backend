from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads token from HTTP-only cookies
    """
    
    def authenticate(self, request):
        # First try to get token from cookie
        raw_token = request.COOKIES.get('access_token')
        
        # If not in cookie, try Authorization header (for backward compatibility)
        if raw_token is None:
            header = self.get_header(request)
            if header is None:
                return None
            
            raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None