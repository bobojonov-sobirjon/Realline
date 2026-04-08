import django_filters
from django.db.models import Q

from apps.accounts.models import PropertyListing, PropertyListingUnit

# Имена тегов для чипов каталога (должны совпадать с tag_name у объявления).
CATALOG_TAG_PROMO = 'Акция'
CATALOG_TAG_START_SALES = 'Старт продаж'
CATALOG_TAG_FOREST = 'С выходом в Лес'
CATALOG_TAG_RAILWAY = 'Ж/д станция рядом'


class PropertyListingFilter(django_filters.FilterSet):
    """Фильтры списка объявлений в кабинете агента (`GET .../properties/`)."""

    status = django_filters.ChoiceFilter(
        choices=PropertyListing.Status.choices,
        help_text=(
            'Статус модерации: `moderation` — на проверке, `published` — на витрине, `rejected` — отклонён админом. '
            'Без параметра возвращаются объекты всех статусов.'
        ),
    )
    category = django_filters.NumberFilter(
        field_name='category_id',
        help_text='ID категории витрины (см. GET /catalog/categories/).',
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact',
        help_text='Slug категории без учёта регистра (например `new_building`, `land_plot`).',
    )
    actual_offers = django_filters.BooleanFilter(
        field_name='is_actual_offer',
        help_text='`true` — только с флагом «Актуальные предложения»; `false` — только без него.',
    )

    class Meta:
        model = PropertyListing
        fields = ('status', 'category', 'category_slug', 'actual_offers')


class PropertyCatalogFilter(django_filters.FilterSet):
    """
    Публичный каталог: только опубликованные объекты.
    Query-параметры как на витрине: тип, район, шоссе, площадь и цена (диапазон), чипы-теги.
    """

    category = django_filters.NumberFilter(
        field_name='category_id',
        help_text='ID категории из GET /catalog/categories/.',
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='iexact',
        help_text='Тот же выбор категории по slug (`new_building`, `land_plot`, …), регистр не важен.',
    )
    property_type = django_filters.ChoiceFilter(
        choices=PropertyListing.PropertyType.choices,
        help_text='Тип объекта для фильтра: `land`, `house`, `apartment`, `commercial`, `other`.',
    )
    district = django_filters.NumberFilter(
        field_name='district_id',
        help_text='ID района из GET /catalog/districts/.',
    )
    highway = django_filters.NumberFilter(
        field_name='highway_id',
        help_text='ID шоссе из GET /catalog/highways/.',
    )
    area_min = django_filters.NumberFilter(
        field_name='area',
        lookup_expr='gte',
        help_text='Минимальная площадь дома/объекта, м².',
    )
    area_max = django_filters.NumberFilter(
        field_name='area',
        lookup_expr='lte',
        help_text='Максимальная площадь дома/объекта, м².',
    )
    land_area_min = django_filters.NumberFilter(
        field_name='land_area',
        lookup_expr='gte',
        help_text='Минимальная площадь участка, сотки.',
    )
    land_area_max = django_filters.NumberFilter(
        field_name='land_area',
        lookup_expr='lte',
        help_text='Максимальная площадь участка, сотки.',
    )
    distance_to_mkad_max = django_filters.NumberFilter(
        field_name='distance_to_mkad_km',
        lookup_expr='lte',
        help_text='Не дальше N км от МКАД (поле объекта distance_to_mkad_km ≤ N).',
    )
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        help_text='Минимальная цена объекта, ₽.',
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        help_text='Максимальная цена объекта, ₽.',
    )

    promo = django_filters.BooleanFilter(
        method='filter_promo',
        help_text='При `true` — только объекты с тегом «Акция» (регистр тега не важен).',
    )
    start_sales = django_filters.BooleanFilter(
        method='filter_start_sales',
        help_text='При `true` — только объекты с тегом «Старт продаж».',
    )
    forest_access = django_filters.BooleanFilter(
        method='filter_forest_access',
        help_text='При `true` — только объекты с тегом «С выходом в Лес».',
    )
    near_railway = django_filters.BooleanFilter(
        method='filter_near_railway',
        help_text='При `true` — только объекты с тегом «Ж/д станция рядом».',
    )

    has_asphalt_roads = django_filters.BooleanFilter(
        help_text='Асфальтированные дороги на территории/посёлке.',
    )
    has_street_lighting = django_filters.BooleanFilter(
        help_text='Уличное освещение.',
    )
    has_guarded_territory = django_filters.BooleanFilter(
        help_text='Охраняемая территория.',
    )
    near_shops = django_filters.BooleanFilter(
        help_text='Магазины рядом.',
    )
    near_school_kindergarten = django_filters.BooleanFilter(
        help_text='Школа и детский сад рядом.',
    )
    near_public_transport = django_filters.BooleanFilter(
        help_text='Остановка общественного транспорта рядом.',
    )

    actual_offers = django_filters.BooleanFilter(
        field_name='is_actual_offer',
        help_text='`true` — объект отмечен для блока «Актуальные предложения» на главной.',
    )

    class Meta:
        model = PropertyListing
        fields = (
            'category',
            'category_slug',
            'property_type',
            'district',
            'highway',
            'area_min',
            'area_max',
            'land_area_min',
            'land_area_max',
            'distance_to_mkad_max',
            'price_min',
            'price_max',
            'promo',
            'start_sales',
            'forest_access',
            'near_railway',
            'has_asphalt_roads',
            'has_street_lighting',
            'has_guarded_territory',
            'near_shops',
            'near_school_kindergarten',
            'near_public_transport',
            'actual_offers',
        )

    def filter_promo(self, queryset, name, value):
        if value:
            return queryset.filter(tags__tag_name__iexact=CATALOG_TAG_PROMO).distinct()
        return queryset

    def filter_start_sales(self, queryset, name, value):
        if value:
            return queryset.filter(tags__tag_name__iexact=CATALOG_TAG_START_SALES).distinct()
        return queryset

    def filter_forest_access(self, queryset, name, value):
        if value:
            return queryset.filter(tags__tag_name__iexact=CATALOG_TAG_FOREST).distinct()
        return queryset

    def filter_near_railway(self, queryset, name, value):
        if value:
            return queryset.filter(tags__tag_name__iexact=CATALOG_TAG_RAILWAY).distinct()
        return queryset


class ListingUnitFilter(django_filters.FilterSet):
    """Фильтры списка лотов ЖК: GET .../catalog/properties/{id}/units/ и .../units/summary/."""

    q = django_filters.CharFilter(
        method='filter_q',
        help_text='Поиск по подстроке: название лота, корпус, группа планировки, отделка (без учёта регистра).',
    )
    building = django_filters.CharFilter(
        field_name='building',
        lookup_expr='icontains',
        help_text='Корпус/литер: вхождение подстроки.',
    )
    layout_label = django_filters.CharFilter(
        field_name='layout_label',
        lookup_expr='iexact',
        help_text='Группа аккордеона (например «Студия»): точное совпадение без учёта регистра.',
    )
    rooms = django_filters.NumberFilter(
        help_text='Точное число комнат.',
    )
    rooms_min = django_filters.NumberFilter(
        field_name='rooms',
        lookup_expr='gte',
        help_text='Минимальное число комнат.',
    )
    rooms_max = django_filters.NumberFilter(
        field_name='rooms',
        lookup_expr='lte',
        help_text='Максимальное число комнат.',
    )
    is_studio = django_filters.BooleanFilter(
        help_text='`true` / `false`: только студии или только не-студии.',
    )
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        help_text='Минимальная цена лота, ₽.',
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        help_text='Максимальная цена лота, ₽.',
    )
    area_min = django_filters.NumberFilter(
        field_name='total_area',
        lookup_expr='gte',
        help_text='Минимальная общая площадь лота, м².',
    )
    area_max = django_filters.NumberFilter(
        field_name='total_area',
        lookup_expr='lte',
        help_text='Максимальная общая площадь лота, м².',
    )
    kitchen_min = django_filters.NumberFilter(
        field_name='kitchen_area',
        lookup_expr='gte',
        help_text='Минимальная площадь кухни, м².',
    )
    kitchen_max = django_filters.NumberFilter(
        field_name='kitchen_area',
        lookup_expr='lte',
        help_text='Максимальная площадь кухни, м².',
    )
    floor = django_filters.NumberFilter(
        help_text='Точный номер этажа.',
    )
    floor_min = django_filters.NumberFilter(
        field_name='floor',
        lookup_expr='gte',
        help_text='Минимальный этаж.',
    )
    floor_max = django_filters.NumberFilter(
        field_name='floor',
        lookup_expr='lte',
        help_text='Максимальный этаж.',
    )
    finishing = django_filters.CharFilter(
        field_name='finishing',
        lookup_expr='icontains',
        help_text='Подстрока в поле отделки лота.',
    )
    is_assignment = django_filters.BooleanFilter(
        help_text='Переуступка.',
    )
    is_two_level = django_filters.BooleanFilter(
        help_text='Двухуровневая планировка.',
    )
    has_master_bedroom = django_filters.BooleanFilter(
        help_text='Мастер-спальня.',
    )
    is_apartments_legal = django_filters.BooleanFilter(
        help_text='Признак апартаментов в карточке лота.',
    )

    class Meta:
        model = PropertyListingUnit
        fields = (
            'q',
            'building',
            'layout_label',
            'rooms',
            'rooms_min',
            'rooms_max',
            'is_studio',
            'price_min',
            'price_max',
            'area_min',
            'area_max',
            'kitchen_min',
            'kitchen_max',
            'floor',
            'floor_min',
            'floor_max',
            'finishing',
            'is_assignment',
            'is_two_level',
            'has_master_bedroom',
            'is_apartments_legal',
        )

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset
        v = value.strip()
        if not v:
            return queryset
        return queryset.filter(
            Q(title__icontains=v)
            | Q(building__icontains=v)
            | Q(layout_label__icontains=v)
            | Q(finishing__icontains=v)
        )
