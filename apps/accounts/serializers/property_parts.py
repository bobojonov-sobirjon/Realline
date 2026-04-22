from rest_framework import serializers

from apps.accounts.models import District, Highway, PropertyCategory, PropertyImage, PropertyTag


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
        fields = ('id', 'name', 'region')


class HighwayRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highway
        fields = ('id', 'name', 'region')


class PropertyCategoryRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCategory
        fields = ('id', 'name', 'slug', 'sort_order')
