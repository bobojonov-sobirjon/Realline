from rest_framework import serializers

from apps.accounts.models import PropertyListingRejection


class PropertyListingRejectionNoticeSerializer(serializers.ModelSerializer):
    listing_id = serializers.IntegerField(read_only=True)
    listing_code = serializers.CharField(source='listing.code', read_only=True)
    listing_name = serializers.CharField(source='listing.name', read_only=True)

    class Meta:
        model = PropertyListingRejection
        fields = (
            'id',
            'listing_id',
            'listing_code',
            'listing_name',
            'reason',
            'created_at',
            'is_seen',
            'seen_at',
        )
        read_only_fields = (
            'id',
            'listing_id',
            'listing_code',
            'listing_name',
            'reason',
            'created_at',
            'is_seen',
            'seen_at',
        )
