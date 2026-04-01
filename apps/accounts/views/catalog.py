from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.accounts.authentication import OptionalJWTAuthentication
from apps.accounts.filters import PropertyCatalogFilter
from apps.accounts.models import District, Highway, PropertyListing
from apps.accounts.serializers import (
    DistrictRefSerializer,
    HighwayRefSerializer,
    PropertyListingSerializer,
)
from apps.accounts.serializers.property_listing import listing_favorite_compare_context
from apps.accounts.views.schemas import _CATALOG_DESCRIPTION


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
            .select_related('district', 'highway')
            .prefetch_related('images', 'tags')
            .order_by('-created_at')
        )


@extend_schema(
    tags=['Каталог'],
    summary='Справочник районов',
    description='Публично. Список для выпадающего списка «Выберите район» при создании объекта — подставляйте **id** в `district_id`.',
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
    description='Публично. Список для «Выберите шоссе» — **id** в поле `highway_id`.',
    responses={200: HighwayRefSerializer(many=True)},
)
class HighwayListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = ()
    serializer_class = HighwayRefSerializer
    pagination_class = None
    queryset = Highway.objects.all()
