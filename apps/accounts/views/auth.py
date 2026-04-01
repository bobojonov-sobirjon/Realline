from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.serializers import AgentRequestCreateSerializer, AgentTokenObtainSerializer


class _AgentApplicationCreateMixin:
    serializer_class = AgentRequestCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        headers = self.get_success_headers({'id': application.pk})
        return Response(
            {
                'id': application.pk,
                'detail': (
                    'Заявка принята. С вами свяжутся; при одобрении вам выдадут логин и пароль для входа '
                    'в личный кабинет.'
                ),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@extend_schema(
    tags=['Accounts — авторизация'],
    summary='Регистрация / заявка (форма у экрана входа)',
    description=(
        'Публичный эндпоинт (без JWT). Тело JSON: `name`, `phone`, `personal_data_consent` (boolean). '
        'Создаётся только запись-заявка; пользователь в БД не создаётся. После одобрения менеджер вручную '
        'заводит кабинет в админке и передаёт агенту логин и пароль.'
    ),
    request=AgentRequestCreateSerializer,
    responses={201: OpenApiResponse(description='Заявка принята; в ответе id и текст для пользователя.')},
)
class AgentRegisterApplicationView(_AgentApplicationCreateMixin, generics.CreateAPIView):
    pass


@extend_schema(
    tags=['Accounts — авторизация'],
    summary='Вход агента (JWT)',
    description=(
        'Тело JSON: `username`, `password`, `personal_data_consent` (true). '
        'Доступ только если в админке у пользователя включено «Подтверждён администратором». '
        'Ответ: `access`, `refresh`, плюс служебные поля user (см. схему).'
    ),
    request=AgentTokenObtainSerializer,
)
class AgentTokenObtainPairView(TokenObtainPairView):
    serializer_class = AgentTokenObtainSerializer


@extend_schema(
    tags=['Accounts — авторизация'],
    summary='Обновить access-токен',
    description='Тело JSON: `refresh` (строка refresh-токена). Ответ содержит новый `access`.',
    request=TokenRefreshSerializer,
)
class AgentTokenRefreshView(TokenRefreshView):
    pass
