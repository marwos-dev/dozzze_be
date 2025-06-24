from ninja.security import HttpBearer


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        from rest_framework_simplejwt.authentication import JWTAuthentication

        jwt_authenticator = JWTAuthentication()
        validated_token = jwt_authenticator.get_validated_token(token)
        user = jwt_authenticator.get_user(validated_token)
        request.user = user
        return token
