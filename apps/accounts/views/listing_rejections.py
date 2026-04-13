from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import PropertyListingRejection
from apps.accounts.serializers.listing_rejection import PropertyListingRejectionNoticeSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — уведомления'],
        summary='Список уведомлений об отклонении объектов',
        description=(
            'Уведомления для **текущего агента** по его объектам, отклонённым модератором. '
            'Сортировка: **сначала новые** (`created_at` по убыванию). '
            'Поле **`is_seen`** — просмотрел ли агент запись; при открытии **GET …/{id}/** становится `true`.'
        ),
    ),
)
class PropertyListingRejectionNoticeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropertyListingRejectionNoticeSerializer

    def get_queryset(self):
        # Только объекты, где agent = текущий пользователь JWT (как PropertyListing.objects.filter(agent=request.user)).
        return (
            PropertyListingRejection.objects.filter(listing__agent=self.request.user)
            .select_related('listing')
            .order_by('-created_at')
        )


@extend_schema_view(
    get=extend_schema(
        tags=['Accounts — уведомления'],
        summary='Уведомление об отклонении по id',
        description=(
            'Одна запись уведомления, только если объект принадлежит агенту из JWT. '
            'После успешного ответа **`is_seen`** устанавливается в **`true`**, **`seen_at`** — текущее время.'
        ),
    ),
)
class PropertyListingRejectionNoticeDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PropertyListingRejectionNoticeSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        # Только уведомления по listing.agent = request.user; иначе get_object() → 404.
        return PropertyListingRejection.objects.filter(listing__agent=self.request.user).select_related(
            'listing'
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_seen:
            instance.is_seen = True
            instance.seen_at = timezone.now()
            instance.save(update_fields=['is_seen', 'seen_at'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
