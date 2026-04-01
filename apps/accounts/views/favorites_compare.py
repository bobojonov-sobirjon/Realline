from django.db.models import Max
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import PropertyListing, UserCompareListing, UserFavoriteListing
from apps.accounts.serializers import PropertyListingSerializer
from apps.accounts.serializers.favorites_compare import ListingIdWriteSerializer

COMPARE_MAX_ITEMS = 10

_ACC_TAG = ['Accounts — витрина (пользователь)']
_FAV_DESC = (
    'Только **JWT** (как и остальной кабинет). Объекты в ответе — как в публичном каталоге '
    '(полная карточка с `images`, `tags`). В избранное попадают только **опубликованные** объекты.'
)
_CMP_DESC = (
    'Очередь сравнения для авторизованного пользователя. Максимум '
    f'{COMPARE_MAX_ITEMS} объектов; при превышении — `400`. Только **опубликованные** объявления.'
)


def _published_listing_qs():
    return (
        PropertyListing.objects.filter(status=PropertyListing.Status.PUBLISHED)
        .select_related('district', 'highway')
        .prefetch_related('images', 'tags')
    )


@extend_schema(
    tags=_ACC_TAG,
    summary='Избранное: список объектов',
    description=_FAV_DESC,
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
    description=_FAV_DESC,
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
    description='`listing_id` — id объекта недвижимости (не id строки избранного).',
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
    description=_CMP_DESC,
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
    description=_CMP_DESC,
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
    description='`listing_id` — id объявления.',
    responses={204: OpenApiResponse(description='Удалено'), 404: OpenApiResponse(description='Не было в списке')},
)
class CompareRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id):
        n, _ = UserCompareListing.objects.filter(user=request.user, listing_id=listing_id).delete()
        if not n:
            return Response({'detail': 'Объект не был в сравнении.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
