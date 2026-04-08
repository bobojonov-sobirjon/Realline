from rest_framework import serializers

from apps.accounts.models import PropertyListingUnit


class PropertyListingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyListingUnit
        fields = (
            'id',
            'listing_id',
            'layout_label',
            'title',
            'building',
            'completion_text',
            'keys_handover_text',
            'rooms',
            'is_studio',
            'price',
            'total_area',
            'kitchen_area',
            'floor',
            'floors_total',
            'finishing',
            'bathroom_summary',
            'ceiling_height',
            'balcony_summary',
            'payment_methods',
            'banks',
            'is_apartments_legal',
            'is_assignment',
            'is_two_level',
            'has_master_bedroom',
            'price_per_sqm',
            'image',
            'sort_order',
            'created_at',
        )
        read_only_fields = ('id', 'listing_id', 'price_per_sqm', 'created_at')


class PropertyListingUnitSummaryRowSerializer(serializers.Serializer):
    layout_label = serializers.CharField(allow_blank=True)
    count = serializers.IntegerField()
    area_min = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    area_max = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    price_min = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    price_max = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    price_per_sqm_min = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
