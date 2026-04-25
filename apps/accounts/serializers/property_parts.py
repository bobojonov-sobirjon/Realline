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


class PropertySubCategoryItemSerializer(serializers.ModelSerializer):
    sub_category = serializers.CharField(source='name')

    class Meta:
        model = PropertyCategory
        fields = ('id', 'sub_category')


class PropertyCategoryTreeSerializer(serializers.ModelSerializer):
    main_category = serializers.CharField(source='name')
    sub_category = serializers.SerializerMethodField()

    class Meta:
        model = PropertyCategory
        fields = ('id', 'main_category', 'sub_category')

    def get_sub_category(self, obj):
        qs = getattr(obj, 'subcategories', None)
        if qs is None:
            sub = PropertyCategory.objects.filter(parent=obj).order_by('sort_order', 'name')
        else:
            sub = qs.all().order_by('sort_order', 'name')
        return PropertySubCategoryItemSerializer(sub, many=True).data
