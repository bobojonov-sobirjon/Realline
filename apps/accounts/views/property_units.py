from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.filters import ListingUnitFilter
from apps.accounts.models import PropertyListing, PropertyListingUnit
from apps.accounts.permissions import IsAgentOwner
from apps.accounts.serializers.listing_units import PropertyListingUnitSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Лоты моего объекта (ЖК)',
        description=(
            '**Назначение:** список лотов/квартир внутри одного объекта агента.\n\n'
            '**Доступ:** только владелец объекта (JWT обязателен).'
        ),
        responses={200: PropertyListingUnitSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Создать лот в моём объекте (ЖК)',
        description=(
            '**Назначение:** добавить лот/квартиру в блок «Планировка и цены» для одного объекта.\n\n'
            '**Доступ:** только владелец объекта (JWT обязателен).'
        ),
        request={
            'multipart/form-data': PropertyListingUnitSerializer,
            'application/json': PropertyListingUnitSerializer,
        },
        responses={201: PropertyListingUnitSerializer},
    ),
)
class PropertyListingUnitAgentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    serializer_class = PropertyListingUnitSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ListingUnitFilter

    def _listing(self) -> PropertyListing:
        listing = get_object_or_404(
            PropertyListing.objects.select_related('agent'),
            pk=self.kwargs['pk'],
        )
        self.check_object_permissions(self.request, listing)
        return listing

    def get_queryset(self):
        listing = self._listing()
        return PropertyListingUnit.objects.filter(listing=listing).order_by('sort_order', 'id')

    def perform_create(self, serializer):
        listing = self._listing()
        serializer.save(listing=listing)


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Лот моего объекта (детали)',
        responses={200: PropertyListingUnitSerializer},
    ),
    put=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Полное обновление лота',
        request={
            'multipart/form-data': PropertyListingUnitSerializer,
            'application/json': PropertyListingUnitSerializer,
        },
        responses={200: PropertyListingUnitSerializer},
    ),
    patch=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Частичное обновление лота',
        request={
            'multipart/form-data': PropertyListingUnitSerializer,
            'application/json': PropertyListingUnitSerializer,
        },
        responses={200: PropertyListingUnitSerializer},
    ),
    delete=extend_schema(
        tags=['Accounts — лоты (units)'],
        summary='Удалить лот',
        responses={204: OpenApiResponse(description='Удалено')},
    ),
)
class PropertyListingUnitAgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAgentOwner]
    serializer_class = PropertyListingUnitSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_url_kwarg = 'unit_pk'

    def _listing(self) -> PropertyListing:
        listing = get_object_or_404(
            PropertyListing.objects.select_related('agent'),
            pk=self.kwargs['pk'],
        )
        self.check_object_permissions(self.request, listing)
        return listing

    def get_queryset(self):
        listing = self._listing()
        return PropertyListingUnit.objects.filter(listing=listing)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

