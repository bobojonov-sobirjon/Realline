from rest_framework import serializers

from apps.accounts.models import District, Highway, PropertyImage, PropertyTag


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ('id', 'image', 'sort_order')
        read_only_fields = ('id',)


class PropertyTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyTag
        fields = ('id', 'tag_name')


class DistrictRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('id', 'name')


class HighwayRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highway
        fields = ('id', 'name')
