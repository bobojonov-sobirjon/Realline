import django_filters

from apps.accounts.models import PropertyListing

# Имена тегов для чипов каталога (должны совпадать с tag_name у объявления).
CATALOG_TAG_PROMO = 'Акция'
CATALOG_TAG_START_SALES = 'Старт продаж'
CATALOG_TAG_FOREST = 'С выходом в Лес'
CATALOG_TAG_RAILWAY = 'Ж/д станция рядом'


class PropertyListingFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=PropertyListing.Status.choices)

    class Meta:
        model = PropertyListing
        fields = ('status',)


class PropertyCatalogFilter(django_filters.FilterSet):
    """
    Публичный каталог: только опубликованные объекты.
    Query-параметры как на витрине: тип, район, шоссе, площадь и цена (диапазон), чипы-теги.
    """

    property_type = django_filters.ChoiceFilter(
        choices=PropertyListing.PropertyType.choices,
    )
    district = django_filters.NumberFilter(field_name='district_id')
    highway = django_filters.NumberFilter(field_name='highway_id')
    area_min = django_filters.NumberFilter(field_name='area', lookup_expr='gte')
    area_max = django_filters.NumberFilter(field_name='area', lookup_expr='lte')
    land_area_min = django_filters.NumberFilter(field_name='land_area', lookup_expr='gte')
    land_area_max = django_filters.NumberFilter(field_name='land_area', lookup_expr='lte')
    distance_to_mkad_max = django_filters.NumberFilter(
        field_name='distance_to_mkad_km', lookup_expr='lte'
    )
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    promo = django_filters.BooleanFilter(method='filter_promo')
    start_sales = django_filters.BooleanFilter(method='filter_start_sales')
    forest_access = django_filters.BooleanFilter(method='filter_forest_access')
    near_railway = django_filters.BooleanFilter(method='filter_near_railway')

    has_asphalt_roads = django_filters.BooleanFilter()
    has_street_lighting = django_filters.BooleanFilter()
    has_guarded_territory = django_filters.BooleanFilter()
    near_shops = django_filters.BooleanFilter()
    near_school_kindergarten = django_filters.BooleanFilter()
    near_public_transport = django_filters.BooleanFilter()

    class Meta:
        model = PropertyListing
        fields = (
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
