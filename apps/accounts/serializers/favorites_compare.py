from rest_framework import serializers

from apps.accounts.models import PropertyListing


class ListingIdWriteSerializer(serializers.Serializer):
    property_listing = serializers.IntegerField(
        min_value=1,
        help_text='ID объекта из каталога (`GET .../catalog/properties/` или поле `id` в карточке). '
        'Учитываются только **опубликованные** объекты.',
    )

    def validate_property_listing(self, value):
        if not PropertyListing.objects.filter(pk=value, status=PropertyListing.Status.PUBLISHED).exists():
            raise serializers.ValidationError('Объект не найден или не опубликован.')
        return value
