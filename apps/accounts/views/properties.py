from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.filters import PropertyListingFilter
from apps.accounts.models import PropertyListing
from apps.accounts.permissions import IsAgentOwner
from apps.accounts.serializers import (
    PropertyListingSerializer,
    PropertyListingUpdateSerializer,
    PropertyListingWriteSerializer,
    PropertyTagSerializer,
    PropertyTagsReplaceSerializer,
    normalize_tags_input_to_sync,
)
from apps.accounts.utils.property_tags import sync_property_tags
from apps.accounts.views.schemas import (
    _AGENT_LIST_FILTERS_DESCRIPTION,
    _PROPERTY_BODY_DESCRIPTION,
    _PROPERTY_DETAIL_DESCRIPTION,
)


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — объекты'],
        summary='Список моих объектов',
        description=(
            '**Назначение:** список объявлений **текущего агента** (владелец = пользователь из JWT).\n\n'
            '**Авторизация:** обязателен **Bearer access-токен** (роль агента с флагом подтверждения в админке).\n\n'
            '**Статусы:** здесь видны **все** ваши карточки — «на модерации», «опубликован», «отклонён» — '
            'в отличие от публичного каталога, где только опубликованные.\n\n'
            f'{_AGENT_LIST_FILTERS_DESCRIPTION}\n\n'
            '**Публичная витрина** (объекты всех агентов, только опубликованные): '
            '`GET .../catalog/properties/`, `GET .../properties/published/`; карточка: '
            '`GET .../catalog/properties/{id}/` или `GET .../properties/published/{id}/`.'
        ),
    ),
    post=extend_schema(
        tags=['Accounts — объекты'],
        summary='Создать объект (отправка на модерацию)',
        description=(
            '**Назначение:** создание новой карточки недвижимости от имени вошедшего агента. '
            'После успешного сохранения объект обычно получает статус **«На модерации»** до проверки администратором.\n\n'
            f'{_PROPERTY_BODY_DESCRIPTION}'
        ),
        request={
            'multipart/form-data': PropertyListingWriteSerializer,
            'application/json': PropertyListingWriteSerializer,
        },
        responses={201: PropertyListingSerializer},
    ),
)
class PropertyListingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyListingFilter
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return (
            PropertyListing.objects.filter(agent=self.request.user)
            .select_related('district', 'highway', 'category')
            .prefetch_related('images', 'tags')
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PropertyListingWriteSerializer
        return PropertyListingSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)
        inst = serializer.instance
        if inst.status == PropertyListing.Status.MODERATION:
            from apps.accounts.utils.moderation_notify import schedule_new_listing_moderation_email

            schedule_new_listing_moderation_email(inst.pk)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read = PropertyListingSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(read.data)
        return Response(read.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — объекты'],
        summary='Карточка объекта',
        description=(
            '**Назначение:** получить одну карточку по **id** в контексте личного кабинета.\n\n'
            '**Доступ:** только **владелец** (агент-владелец записи); иначе **403/404**. JWT обязателен.\n\n'
            'В ответе полная структура как в каталоге: фото, теги, уникальный код объекта (формат RL- и четыре цифры), '
            'детали категории, плюс актуальный **status** и **rejection_reason** при отклонении.'
        ),
        responses={200: PropertyListingSerializer},
    ),
    put=extend_schema(
        tags=['Accounts — объекты'],
        summary='Полное обновление объекта',
        description=(
            '**PUT:** заменить карточку целиком — передайте все обязательные и нужные поля модели записи. '
            'Удобно при формах «сохранить всё».\n\n'
            f'{_PROPERTY_DETAIL_DESCRIPTION}'
        ),
        request={
            'multipart/form-data': PropertyListingUpdateSerializer,
            'application/json': PropertyListingUpdateSerializer,
        },
        responses={200: PropertyListingSerializer},
    ),
    patch=extend_schema(
        tags=['Accounts — объекты'],
        summary='Частичное обновление объекта',
        description=(
            '**PATCH:** обновить только изменившиеся поля (и вложенные блоки `residential_details` / '
            '`land_plot_details` частично). Остальные значения на сервере сохраняются.\n\n'
            f'{_PROPERTY_DETAIL_DESCRIPTION}'
        ),
        request={
            'multipart/form-data': PropertyListingUpdateSerializer,
            'application/json': PropertyListingUpdateSerializer,
        },
        responses={200: PropertyListingSerializer},
    ),
    delete=extend_schema(
        tags=['Accounts — объекты'],
        summary='Удалить объект',
        description=(
            '**DELETE:** полное удаление объявления из базы. Связанные **изображения** и файлы с диска '
            'удаляются каскадно (в пределах модели). Операция **необратима**. Доступ только владельцу.'
        ),
        responses={204: OpenApiResponse(description='Удалено')},
    ),
)
class PropertyListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    lookup_field = 'pk'
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return (
            PropertyListing.objects.filter(agent=self.request.user)
            .select_related('district', 'highway', 'category')
            .prefetch_related('images', 'tags')
        )

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PropertyListingUpdateSerializer
        return PropertyListingSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        read = PropertyListingSerializer(instance, context={'request': request})
        return Response(read.data)


@extend_schema(
    tags=['Accounts — объекты'],
    summary='Заменить все теги объекта',
    description=(
        '**Назначение:** быстро обновить только маркетинговые **теги** (чипы на витрине) без остальных полей карточки.\n\n'
        '**Метод:** `PUT`. Тело JSON: `{"tags": ["лес", "дача"]}` или `multipart/form-data` с повторяющимся полем **`tags`**. '
        'Список имён задаёт **итоговый** набор: прежние теги объекта удаляются, создаются новые записи '
        '(в ответе у элементов будут **новые** `id`).\n\n'
        '**`{"tags": []}`** — удалить все теги у объекта.\n\n'
        '**Ответ:** массив `[{ "id", "tag_name" }, …]` в актуальном порядке. Некоторые имена тегов участвуют в '
        'фильтрах каталога (`promo`, `start_sales` и т.д.) — см. описание каталога.'
    ),
    request=PropertyTagsReplaceSerializer,
    responses={200: OpenApiResponse(description='Массив тегов [{id, tag_name}, ...]')},
)
class PropertyTagsReplaceView(APIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def put(self, request, pk):
        listing = get_object_or_404(PropertyListing.objects.filter(agent=request.user), pk=pk)
        self.check_object_permissions(request, listing)
        data = request.data
        tl = request.POST.getlist('tags') if hasattr(request, 'POST') else []
        if tl and hasattr(data, 'copy') and hasattr(data, 'setlist'):
            data = data.copy()
            data.setlist('tags', tl)
        serializer = PropertyTagsReplaceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        sync_property_tags(
            listing,
            normalize_tags_input_to_sync(serializer.validated_data['tags']),
        )
        return Response(PropertyTagSerializer(listing.tags.all(), many=True).data)


@extend_schema(
    tags=['Accounts — объекты'],
    summary='Снять объект с публикации',
    description=(
        '**POST** без тела. Только **владелец** объекта.\n\n'
        'Статус карточки переводится в **«На модерации»**; объект исчезает с публичной витрины '
        '(каталог и публичные детали вернут **404** по id). Используется как «снять с публикации» без удаления данных.'
    ),
    responses={200: PropertyListingSerializer},
)
class PropertyUnpublishView(APIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    serializer_class = PropertyListingSerializer

    def post(self, request, pk):
        listing = get_object_or_404(PropertyListing.objects.filter(agent=request.user), pk=pk)
        self.check_object_permissions(request, listing)
        listing.status = PropertyListing.Status.MODERATION
        listing.save(update_fields=['status', 'updated_at'])
        return Response(PropertyListingSerializer(listing, context={'request': request}).data)


@extend_schema(
    tags=['Accounts — объекты'],
    summary='Повторно отправить на модерацию',
    description=(
        '**POST** без тела. Владелец может вызвать после **отклонения** админом.\n\n'
        'Статус снова **«На модерации»**, поле **`rejection_reason`** очищается. Дальнейшее решение — в админке '
        '(повторная публикация или снова отклонение).'
    ),
    responses={200: PropertyListingSerializer},
)
class PropertyResubmitView(APIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    serializer_class = PropertyListingSerializer

    def post(self, request, pk):
        listing = get_object_or_404(PropertyListing.objects.filter(agent=request.user), pk=pk)
        self.check_object_permissions(request, listing)
        listing.status = PropertyListing.Status.MODERATION
        listing.rejection_reason = ''
        listing.save(update_fields=['status', 'rejection_reason', 'updated_at'])
        return Response(PropertyListingSerializer(listing, context={'request': request}).data)
