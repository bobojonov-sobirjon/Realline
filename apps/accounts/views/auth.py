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
        '**Назначение:** приём заявки от потенциального агента с публичной формы («стать партнёром» / регистрация).\n\n'
        '**Доступ:** без токена. Тело **JSON**: имя, телефон, флаг согласия на обработку персональных данных '
        '(`personal_data_consent`, должен быть `true` при действующей политике).\n\n'
        '**Побочный эффект:** в таблице заявок создаётся одна запись; **учётная запись пользователя не создаётся** '
        'автоматически. После проверки менеджер в **админке Django** создаёт пользователя агента и выдаёт логин/пароль.\n\n'
        '**Ответ:** HTTP 201, поля `id` заявки и человекочитаемое сообщение для экрана успеха.'
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
        '**Назначение:** получить пару **access** / **refresh** JWT для вызовов защищённых методов API '
        '(кабинет агента, избранное, сравнение).\n\n'
        '**Тело JSON:** `username` (как при выдаче кабинета), `password`, `personal_data_consent`: **true** '
        '(единоразовое подтверждение политики при входе).\n\n'
        '**Условие:** у пользователя в админке должен быть флаг **«Подтверждён администратором»** (`is_verified`); '
        'иначе вход будет отклонён.\n\n'
        '**Ответ:** короткоживущий **access** (заголовок `Authorization: Bearer ...`) и **refresh** для продления сессии '
        'через `POST .../token/refresh/`; при необходимости дополнительные поля профиля — см. схему ответа сериализатора.'
    ),
    request=AgentTokenObtainSerializer,
)
class AgentTokenObtainPairView(TokenObtainPairView):
    serializer_class = AgentTokenObtainSerializer


@extend_schema(
    tags=['Accounts — авторизация'],
    summary='Обновить access-токен',
    description=(
        '**Назначение:** получить новый **access**-токен без повторного ввода пароля, пока действителен **refresh**.\n\n'
        '**Тело JSON:** объект с полем **`refresh`** — строка refresh-токена, выданная при логине.\n\n'
        '**Ответ:** новый **access** (и при настройках SimpleJWT может вращаться refresh — см. фактический JSON). '
        'Используйте новый access в заголовке `Authorization: Bearer ...` для всех последующих запросов.'
    ),
    request=TokenRefreshSerializer,
)
class AgentTokenRefreshView(TokenRefreshView):
    pass
