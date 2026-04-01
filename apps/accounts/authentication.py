"""Аутентификация для публичных эндпоинтов с опциональным JWT."""

from typing import Optional

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class OptionalJWTAuthentication(JWTAuthentication):
    """
    Как JWTAuthentication, но при отсутствии заголовка или при невалидном токене
    возвращает None (аноним), а не 401 — совместимо с AllowAny на витрине каталога.
    """

    def authenticate(self, request: Request) -> Optional[tuple]:
        header = self.get_header(request)
        if header is None:
            return None
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None
