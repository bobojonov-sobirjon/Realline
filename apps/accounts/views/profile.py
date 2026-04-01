from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    AgentProfileSerializer,
    AgentProfileUpdateSerializer,
    ChangePasswordSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — профиль'],
        summary='Профиль агента',
        description=(
            'Требуется Bearer JWT. Возвращает `full_name`, `phone`, `description`, `email`, `username`, `is_verified`.'
        ),
        responses={200: AgentProfileSerializer},
    ),
    put=extend_schema(
        tags=['Accounts — профиль'],
        summary='Полное обновление профиля',
        description='JSON: все поля профиля; `email` можно сменить — обновится у пользователя.',
        request=AgentProfileUpdateSerializer,
        responses={200: AgentProfileSerializer},
    ),
    patch=extend_schema(
        tags=['Accounts — профиль'],
        summary='Частичное обновление профиля',
        description='JSON: передайте только изменяемые поля (`full_name`, `phone`, `description`, `email`).',
        request=AgentProfileUpdateSerializer,
        responses={200: AgentProfileSerializer},
    ),
)
class AgentProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'put', 'head', 'options']

    def get_object(self):
        return self.request.user.agent_profile

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AgentProfileUpdateSerializer
        return AgentProfileSerializer


@extend_schema(
    tags=['Accounts — профиль'],
    summary='Смена пароля',
    description=(
        'Требуется Bearer JWT; старый пароль не спрашивается. '
        'Тело (JSON или form): `new_password`, `new_password_confirm` (мин. 8 символов, правила Django).'
    ),
    request=ChangePasswordSerializer,
    responses={200: OpenApiResponse(description='Пароль обновлён; дальнейшие запросы — с новым паролем при логине.')},
)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Пароль успешно обновлён.'})
