from django.db.models import Max
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PropertyListing, UserCompareListing, UserFavoriteListing
from apps.accounts.serializers import PropertyListingSerializer
from apps.accounts.serializers.favorites_compare import ListingIdWriteSerializer

COMPARE_MAX_ITEMS = 5

_ACC_TAG = ['Accounts — витрина (пользователь)']
_FAV_DESC = (
    '**Избранное** привязано к учётной записи агента. Обязателен **JWT**.\n\n'
    'В списке и при добавлении возвращаются **полные карточки** как в каталоге (`PropertyListingSerializer`: фото, теги, '
    'район, цена и т.д.). В избранное **можно добавить только опубликованный** объект; неопубликованный id даст ошибку '
    'при получении полной карточки из витрины.\n\n'
    'Порядок элементов в **GET** — от новых добавлений к старым.'
)
_CMP_DESC = (
    '**Сравнение** — до '
    f'**{COMPARE_MAX_ITEMS}** опубликованных объявлений на пользователя. При попытке добавить сверх лимита — **HTTP 400** '
    'с текстом причины. Повторное добавление того же id не дублирует запись (идемпотентно возвращается текущая карточка).\n\n'
    'Обязателен **JWT**. Формат карточек такой же, как в каталоге.'
)


def _published_listing_qs():
    return (
        PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED)
        .select_related('district', 'highway', 'category')
        .prefetch_related('images', 'tags')
    )


@extend_schema(
    tags=_ACC_TAG,
    summary='Избранное: список объектов',
    description='**GET** — массив объектов в избранном.\n\n' + _FAV_DESC,
    responses={200: PropertyListingSerializer(many=True)},
)
class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listing_ids = UserFavoriteListing.objects.filter(user=request.user).order_by('-created_at').values_list(
            'listing_id', flat=True
        )
        id_order = {pk: i for i, pk in enumerate(listing_ids)}
        qs = _published_listing_qs().filter(pk__in=listing_ids)
        listings = sorted(qs, key=lambda x: id_order.get(x.pk, 0))
        ser = PropertyListingSerializer(listings, many=True, context={'request': request})
        return Response(ser.data)


@extend_schema(
    tags=_ACC_TAG,
    summary='Избранное: добавить объект',
    description=(
        '**POST** с телом `{"property_listing": <id>}`. Создаёт связь пользователь–объект; если уже в избранном — **200** '
        'и актуальная карточка, если новая — **201**.\n\n' + _FAV_DESC
    ),
    request=ListingIdWriteSerializer,
    responses={201: PropertyListingSerializer},
)
class FavoriteAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        w = ListingIdWriteSerializer(data=request.data)
        w.is_valid(raise_exception=True)
        lid = w.validated_data['property_listing']
        listing = PropertyListing.objects.get(pk=lid)
        _fav, created = UserFavoriteListing.objects.get_or_create(user=request.user, listing=listing)
        listing_full = _published_listing_qs().get(pk=lid)
        return Response(
            PropertyListingSerializer(listing_full, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema(
    tags=_ACC_TAG,
    summary='Избранное: убрать объект',
    description=(
        '**DELETE** по пути с **`listing_id` в URL** — это **первичный ключ объекта** `PropertyListing`, '
        'а не внутренний id записи избранного.\n\n'
        '**204** — удалено; **404** — такой объект не был в избранном.'
    ),
    responses={204: OpenApiResponse(description='Удалено'), 404: OpenApiResponse(description='Не было в избранном')},
)
class FavoriteRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id):
        n, _ = UserFavoriteListing.objects.filter(user=request.user, listing_id=listing_id).delete()
        if not n:
            return Response({'detail': 'Объект не был в избранном.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=_ACC_TAG,
    summary='Сравнение: список объектов',
    description='**GET** — текущая корзина сравнения в порядке сохранённых позиций.\n\n' + _CMP_DESC,
    responses={200: PropertyListingSerializer(many=True)},
)
class CompareListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = UserCompareListing.objects.filter(user=request.user).order_by('sort_order', 'id')
        listing_ids = list(links.values_list('listing_id', flat=True))
        if not listing_ids:
            return Response([])
        id_order = {pk: i for i, pk in enumerate(listing_ids)}
        qs = _published_listing_qs().filter(pk__in=listing_ids)
        listings = sorted(qs, key=lambda x: id_order.get(x.pk, 0))
        ser = PropertyListingSerializer(listings, many=True, context={'request': request})
        return Response(ser.data)


@extend_schema(
    tags=_ACC_TAG,
    summary='Сравнение: добавить объект',
    description=(
        '**POST** с `{"property_listing": <id>}`. Учитывается лимит корзины; при успехе возвращается полная карточка.\n\n'
        + _CMP_DESC
    ),
    request=ListingIdWriteSerializer,
    responses={
        201: PropertyListingSerializer,
        400: OpenApiResponse(description='Лимит сравнения превышен'),
    },
)
class CompareAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        w = ListingIdWriteSerializer(data=request.data)
        w.is_valid(raise_exception=True)
        lid = w.validated_data['property_listing']
        listing = PropertyListing.objects.get(pk=lid)

        if UserCompareListing.objects.filter(user=request.user, listing_id=lid).exists():
            listing_full = _published_listing_qs().get(pk=lid)
            return Response(
                PropertyListingSerializer(listing_full, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )

        count = UserCompareListing.objects.filter(user=request.user).count()
        if count >= COMPARE_MAX_ITEMS:
            return Response(
                {'detail': f'В сравнении не более {COMPARE_MAX_ITEMS} объектов.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_so = UserCompareListing.objects.filter(user=request.user).aggregate(m=Max('sort_order'))['m']
        UserCompareListing.objects.create(
            user=request.user,
            listing=listing,
            sort_order=(max_so or 0) + 1,
        )
        listing_full = _published_listing_qs().get(pk=lid)
        return Response(
            PropertyListingSerializer(listing_full, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=_ACC_TAG,
    summary='Сравнение: убрать объект',
    description=(
        '**DELETE**: **`listing_id`** в пути — id объекта **`PropertyListing`**.\n\n'
        '**204** если запись сравнения удалена; **404** если объекта не было в списке.'
    ),
    responses={204: OpenApiResponse(description='Удалено'), 404: OpenApiResponse(description='Не было в списке')},
)
class CompareRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id):
        n, _ = UserCompareListing.objects.filter(user=request.user, listing_id=listing_id).delete()
        if not n:
            return Response({'detail': 'Объект не был в сравнении.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _as_bool(v):
    if v is None:
        return None
    return bool(v)


def _first_image_url(listing: PropertyListing, request):
    images_mgr = getattr(listing, 'images', None)
    if images_mgr is None or not hasattr(images_mgr, 'all'):
        return None
    img = images_mgr.all().first()
    if not img or not getattr(img, 'image', None):
        return None
    url = img.image.url
    return request.build_absolute_uri(url) if request else url


def _label_or_none(ref_obj, attr='name'):
    if not ref_obj:
        return None
    return getattr(ref_obj, attr, None)


def _compare_row(key: str, label: str, row_type: str, listings: list[PropertyListing], getter):
    return {
        'key': key,
        'label': label,
        'type': row_type,
        'values': [getter(x) for x in listings],
    }


@extend_schema(
    tags=_ACC_TAG,
    summary='Сравнение: данные для таблицы сравнения',
    description=(
        'Возвращает корзину сравнения в формате, удобном для построения таблицы: '
        'вверху — список объектов (колонки), ниже — строки с полями и значениями.\n\n' + _CMP_DESC
    ),
    responses={200: OpenApiResponse(description='Структура таблицы сравнения')},
)
class CompareTableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        links = UserCompareListing.objects.filter(user=request.user).order_by('sort_order', 'id')
        listing_ids = list(links.values_list('listing_id', flat=True))
        if not listing_ids:
            return Response({'items': [], 'rows': []})

        id_order = {pk: i for i, pk in enumerate(listing_ids)}
        qs = _published_listing_qs().filter(pk__in=listing_ids).select_related(
            'residential_details',
            'land_plot_details',
        )
        listings = sorted(qs, key=lambda x: id_order.get(x.pk, 0))

        items = [
            {
                'id': x.pk,
                'code': x.code,
                'name': x.name,
                'price': x.price,
                'image': _first_image_url(x, request),
            }
            for x in listings
        ]

        rows = [
            _compare_row('category', 'Категория', 'text', listings, lambda x: _label_or_none(x.category)),
            _compare_row('property_type', 'Тип', 'text', listings, lambda x: x.get_property_type_display() if hasattr(x, 'get_property_type_display') else x.property_type),
            _compare_row('settlement', 'Населённый пункт', 'text', listings, lambda x: x.settlement or None),
            _compare_row('district', 'Район', 'text', listings, lambda x: _label_or_none(x.district)),
            _compare_row('highway', 'Шоссе', 'text', listings, lambda x: _label_or_none(x.highway)),
            _compare_row('address', 'Адрес', 'text', listings, lambda x: x.address or None),
            _compare_row('area', 'Площадь объекта, м²', 'number', listings, lambda x: x.area),
            _compare_row('land_area', 'Площадь участка, сот.', 'number', listings, lambda x: x.land_area),
            _compare_row('distance_to_mkad_km', 'До МКАД, км', 'number', listings, lambda x: x.distance_to_mkad_km),
            _compare_row('floors', 'Этажей', 'number', listings, lambda x: x.floors),
            _compare_row('rooms', 'Комнат', 'number', listings, lambda x: x.rooms),
            _compare_row('bedrooms', 'Спален', 'number', listings, lambda x: x.bedrooms),
            _compare_row('bathrooms', 'Санузлов', 'number', listings, lambda x: x.bathrooms),
            _compare_row('year_built', 'Год постройки', 'number', listings, lambda x: x.year_built),
            _compare_row('wall_material', 'Материал стен', 'text', listings, lambda x: x.wall_material or None),
            _compare_row('finishing', 'Отделка', 'text', listings, lambda x: x.finishing or None),
            _compare_row('electricity_supply', 'Электричество', 'text', listings, lambda x: x.electricity_supply or None),
            _compare_row('water_supply', 'Водоснабжение', 'text', listings, lambda x: x.water_supply or None),
            _compare_row('sewage_type', 'Канализация', 'text', listings, lambda x: x.sewage_type or None),
            _compare_row('heating_type', 'Отопление', 'text', listings, lambda x: x.heating_type or None),
            _compare_row('internet_connection', 'Интернет', 'text', listings, lambda x: x.internet_connection or None),
            _compare_row('has_asphalt_roads', 'Асфальтированные дороги', 'bool', listings, lambda x: _as_bool(x.has_asphalt_roads)),
            _compare_row('has_street_lighting', 'Уличное освещение', 'bool', listings, lambda x: _as_bool(x.has_street_lighting)),
            _compare_row('has_guarded_territory', 'Охраняемая территория', 'bool', listings, lambda x: _as_bool(x.has_guarded_territory)),
            _compare_row('near_shops', 'Магазины рядом', 'bool', listings, lambda x: _as_bool(x.near_shops)),
            _compare_row('near_school_kindergarten', 'Школа и детский сад рядом', 'bool', listings, lambda x: _as_bool(x.near_school_kindergarten)),
            _compare_row('near_public_transport', 'Остановка ОТ рядом', 'bool', listings, lambda x: _as_bool(x.near_public_transport)),

            # Category-specific blocks (if absent — null)
            _compare_row('residential.developer', 'Застройщик', 'text', listings, lambda x: getattr(getattr(x, 'residential_details', None), 'developer', None) or None),
            _compare_row('residential.completion_period_text', 'Срок сдачи (текст)', 'text', listings, lambda x: getattr(getattr(x, 'residential_details', None), 'completion_period_text', None) or None),
            _compare_row('residential.housing_class', 'Класс жилья', 'text', listings, lambda x: getattr(getattr(x, 'residential_details', None), 'housing_class', None) or None),
            _compare_row('residential.parking_info', 'Паркинг', 'text', listings, lambda x: getattr(getattr(x, 'residential_details', None), 'parking_info', None) or None),
            _compare_row('residential.price_per_sqm_from', 'Цена за м² от, ₽', 'number', listings, lambda x: getattr(getattr(x, 'residential_details', None), 'price_per_sqm_from', None)),

            _compare_row('land.external_reference_id', 'ID на витрине', 'text', listings, lambda x: getattr(getattr(x, 'land_plot_details', None), 'external_reference_id', None) or None),
            _compare_row('land.plot_number', '№ участка', 'text', listings, lambda x: getattr(getattr(x, 'land_plot_details', None), 'plot_number', None) or None),
            _compare_row('land.cadastral_number', 'Кадастровый номер', 'text', listings, lambda x: getattr(getattr(x, 'land_plot_details', None), 'cadastral_number', None) or None),
            _compare_row('land.land_purpose', 'Назначение земли', 'text', listings, lambda x: getattr(getattr(x, 'land_plot_details', None), 'land_purpose', None) or None),
            _compare_row('land.completion_quarter_text', 'Срок сдачи / подключения', 'text', listings, lambda x: getattr(getattr(x, 'land_plot_details', None), 'completion_quarter_text', None) or None),
        ]

        return Response({'items': items, 'rows': rows})
