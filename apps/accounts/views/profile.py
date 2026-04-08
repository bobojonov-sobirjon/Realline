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
            '**GET:** текущие данные профиля агента и учётной записи.\n\n'
            '**Авторизация:** Bearer JWT.\n\n'
            'В ответе: контактные **full_name**, **phone**, текст **description**, а также **email**, **username**, '
            'флаг **is_verified** (подтверждение админом). Структура соответствует `AgentProfileSerializer`.'
        ),
        responses={200: AgentProfileSerializer},
    ),
    put=extend_schema(
        tags=['Accounts — профиль'],
        summary='Полное обновление профиля',
        description=(
            '**PUT:** передать полный набор полей профиля (**full_name**, **phone**, **description**, при необходимости '
            '**email**). Email синхронизируется с моделью пользователя и должен оставаться уникальным.'
        ),
        request=AgentProfileUpdateSerializer,
        responses={200: AgentProfileSerializer},
    ),
    patch=extend_schema(
        tags=['Accounts — профиль'],
        summary='Частичное обновление профиля',
        description=(
            '**PATCH:** только изменившиеся поля (`full_name`, `phone`, `description`, `email`). '
            'Остальные значения не сбрасываются.'
        ),
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
        '**Назначение:** установить новый пароль для **вошедшего** пользователя без ввода старого пароля '
        '(сценарий «восстановление/смена из кабинета» при доверенной сессии).\n\n'
        '**Авторизация:** Bearer JWT.\n\n'
        '**Тело:** JSON или form — **`new_password`**, **`new_password_confirm`** (должны совпадать). '
        'Действуют стандартные **валидаторы паролей Django** (длина, сложность и т.д.).\n\n'
        'После успеха используйте новый пароль при следующем **логине**.'
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
