from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from .models import LineUser


class LineUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            line_user_id = validated_token['line_user_id']
        except KeyError:
            raise InvalidToken('Token missing line_user_id claim')
        try:
            return LineUser.objects.get(line_user_id=line_user_id)
        except LineUser.DoesNotExist:
            raise AuthenticationFailed('User not found')
