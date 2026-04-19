from django.db.models import Count, Max, Min
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.authentication import OptionalJWTAuthentication
from apps.accounts.filters import ListingUnitFilter, PropertyCatalogFilter
from apps.accounts.models import (
    District,
    Highway,
    PropertyCategory,
    PropertyListing,
    PropertyListingUnit,
)
from apps.accounts.serializers import (
    DistrictRefSerializer,
    HighwayRefSerializer,
    PropertyCategoryRefSerializer,
    PropertyListingSerializer,
    PropertyListingUnitSerializer,
    PropertyListingUnitSummaryRowSerializer,
)
from apps.accounts.serializers.property_listing import listing_favorite_compare_context
from apps.accounts.views.schemas import (
    _CATALOG_DESCRIPTION,
    _LISTING_UNITS_DESCRIPTION,
    _LISTING_UNITS_SUMMARY_DESCRIPTION,
)


@extend_schema(
    tags=['Каталог'],
    summary='Каталог объявлений (витрина)',
    description=_CATALOG_DESCRIPTION,
    responses={200: PropertyListingSerializer(many=True)},
)
class PropertyCatalogListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]
    serializer_class = PropertyListingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyCatalogFilter

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update(listing_favorite_compare_context(self.request))
        return ctx

    def get_queryset(self):
        return (
            PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED)
            .select_related('district', 'highway', 'category')
            .prefetch_related(
                'images',
                'tags',
                'units',
                'residential_details',
                'land_plot_details',
            )
            .order_by('-created_at')
        )


@extend_schema(
    tags=['Каталог'],
    summary='Карточка объекта на витрине',
    description=(
        '**Назначение:** одна карточка недвижимости для публичного сайта по числовому **id**.\n\n'
        '**Доступ:** публично; JWT **не обязателен**. Если передать Bearer-токен, в теле будут '
        '**`is_favourite`** и **`is_compare`** для текущего пользователя (как в списке каталога).\n\n'
        '**Статус:** только **«Опубликован»**. Объект на модерации, отклонённый или удалённый — **404**, '
        'чтобы нельзя было увидеть черновик по прямой ссылке.\n\n'
        'Структура ответа совпадает с элементом списка `GET .../catalog/properties/`: изображения, теги, '
        'район, категория, блоки `residential_details` / `land_plot_details` при наличии.'
    ),
    responses={
        200: PropertyListingSerializer,
        404: OpenApiResponse(description='Нет в каталоге (не опубликован или не существует)'),
    },
)
class PropertyCatalogDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWTAuthentication]
    serializer_class = PropertyListingSerializer
    lookup_field = 'pk'

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update(listing_favorite_compare_context(self.request))
        return ctx

    def get_queryset(self):
        return (
            PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED)
            .select_related('district', 'highway', 'category')
            .prefetch_related(
                'images',
                'tags',
                'units',
                'residential_details',
                'land_plot_details',
            )
        )


@extend_schema(
    tags=['Accounts — объекты'],
    summary='Все опубликованные объявления (витрина)',
    description=(
        '**Алиас витрины** под префиксом `/properties/published/`.\n\n'
        'Полностью совпадает с **`GET .../catalog/properties/`**: те же поля, **те же query-фильтры** '
        '(см. описание каталога и подсказки к параметрам в Swagger), пагинация `limit`/`offset`, '
        'сортировка по дате создания. В выборку попадают объекты **всех** агентов только со статусом '
        '**«Опубликован»**.\n\n'
        '**Зачем отдельный путь:** удобно вызывать из кода кабинета рядом с `GET .../properties/` '
        '(список **своих** объявлений с любым статусом), не смешивая URL витрины и ЛК.\n\n'
        'JWT опционален; с токеном — поля **`is_favourite`** и **`is_compare`**.'
    ),
    responses={200: PropertyListingSerializer(many=True)},
)
class PropertyPublishedListView(PropertyCatalogListView):
    """Алиас витрины под префиксом `/properties/published/`."""

    pass


@extend_schema(
    tags=['Accounts — объекты'],
    summary='Карточка опубликованного объекта (витрина)',
    description=(
        '**Алиас карточки витрины:** `GET .../properties/published/{id}/`.\n\n'
        'Логика как у **`GET .../catalog/properties/{id}/`**: только статус **«Опубликован»**, '
        'иначе **404**. Опциональный JWT даёт **`is_favourite`** / **`is_compare`**.\n\n'
        '**Не путать** с **`GET .../properties/{id}/`** (кабинет агента): там доступ **только владельцу** '
        'и допускаются любые статусы (модерация, отклонён и т.д.).'
    ),
    responses={
        200: PropertyListingSerializer,
        404: OpenApiResponse(description='Нет в каталоге'),
    },
)
class PropertyPublishedDetailView(PropertyCatalogDetailView):
    """Алиас карточки витрины: `/properties/published/{id}/`."""

    pass


@extend_schema(
    tags=['Каталог'],
    summary='Справочник категорий витрины',
    description=(
        '**Назначение:** словарь типов объектов для форм и для фильтра каталога (`category`, `category_slug`).\n\n'
        '**Доступ:** публично, без авторизации. Пагинации нет — отдаётся полный активный справочник '
        '(сортировка: `sort_order`, затем название).\n\n'
        '**Поля:** `id`, `name`, `slug`, `sort_order`. При создании/редактировании объекта в API передавайте '
        '**`category_id`** = `id` из этого списка.\n\n'
        '**Важно:** если **slug** = `land_plot`, в карточке объекта используется блок **`land_plot_details`**; '
        'для всех остальных slug — общий блок **`residential_details`** (новостройки, вторичка, загород и т.д.).'
    ),
    responses={200: PropertyCategoryRefSerializer(many=True)},
)
class PropertyCategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    serializer_class = PropertyCategoryRefSerializer
    pagination_class = None
    queryset = PropertyCategory.objects.all().order_by('sort_order', 'name')


@extend_schema(
    tags=['Каталог'],
    summary='Справочник районов',
    description=(
        '**Назначение:** подсказка для поля «Район» в формах и фильтр **`district`** в каталоге (значение = **id** записи).\n\n'
        '**Доступ:** публично. Формат ответа: массив `{ id, name }`. Список отсортирован по названию.\n\n'
        'В теле создания/обновления объекта передаётся **`district_id`**, не текст названия.'
    ),
    responses={200: DistrictRefSerializer(many=True)},
)
class DistrictListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    serializer_class = DistrictRefSerializer
    pagination_class = None
    queryset = District.objects.all()


@extend_schema(
    tags=['Каталог'],
    summary='Справочник шоссе',
    description=(
        '**Назначение:** выбор шоссе при заполнении карточки и фильтр **`highway`** в каталоге.\n\n'
        '**Доступ:** публично. Ответ: `{ id, name }` для каждой записи.\n\n'
        'В API объекта поле **`highway_id`** — внешний ключ на `id` из этого списка; текст шоссе вручную не подставляется.'
    ),
    responses={200: HighwayRefSerializer(many=True)},
)
class HighwayListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    serializer_class = HighwayRefSerializer
    pagination_class = None
    queryset = Highway.objects.all()


class _PublishedListingUnitsMixin:
    listing_kwarg = 'listing_pk'

    def _published_listing(self):
        return get_object_or_404(
            PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED),
            pk=self.kwargs[self.listing_kwarg],
        )

    def units_queryset(self):
        listing = self._published_listing()
        return PropertyListingUnit.objects.filter(listing=listing)


@extend_schema(
    tags=['Каталог'],
    summary='Лоты ЖК («Планировка и цены»)',
    description=_LISTING_UNITS_DESCRIPTION,
    responses={
        200: PropertyListingUnitSerializer(many=True),
        404: OpenApiResponse(description='Объект не в каталоге'),
    },
)
class PropertyListingUnitListView(_PublishedListingUnitsMixin, generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    serializer_class = PropertyListingUnitSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ListingUnitFilter

    def get_queryset(self):
        return self.units_queryset().order_by('sort_order', 'id')


@extend_schema(
    tags=['Каталог'],
    summary='Сводка лотов по группам планировки',
    description=_LISTING_UNITS_SUMMARY_DESCRIPTION,
    responses={
        200: PropertyListingUnitSummaryRowSerializer(many=True),
        404: OpenApiResponse(description='Объект не в каталоге'),
    },
)
class PropertyListingUnitSummaryView(_PublishedListingUnitsMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request, *args, **kwargs):
        qs = ListingUnitFilter(request.query_params, queryset=self.units_queryset()).qs
        rows = (
            qs.values('layout_label')
            .annotate(
                count=Count('id'),
                area_min=Min('total_area'),
                area_max=Max('total_area'),
                price_min=Min('price'),
                price_max=Max('price'),
                price_per_sqm_min=Min('price_per_sqm'),
            )
            .order_by('layout_label')
        )
        return Response(list(rows))
