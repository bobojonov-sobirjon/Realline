from rest_framework import serializers

from apps.accounts.filters import (
    CATALOG_TAG_FOREST,
    CATALOG_TAG_PROMO,
    CATALOG_TAG_RAILWAY,
    CATALOG_TAG_START_SALES,
)
from apps.accounts.models import (
    District,
    Highway,
    PropertyImage,
    PropertyListing,
    UserCompareListing,
    UserFavoriteListing,
)
from apps.accounts.serializers.property_parts import (
    DistrictRefSerializer,
    HighwayRefSerializer,
    PropertyImageSerializer,
    PropertyTagSerializer,
)
from apps.accounts.serializers.tags_parsing import coalesce_multipart_tags, normalize_tags_input_to_sync
from apps.accounts.utils.property_tags import sync_property_tags


def listing_favorite_compare_context(request) -> dict:
    """ID множества для is_favourite / is_compare у текущего пользователя (2 запроса на сериализацию)."""
    empty = frozenset()
    if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'favorite_listing_ids': empty, 'compare_listing_ids': empty}
    user = request.user
    fav = frozenset(
        UserFavoriteListing.objects.filter(user=user).values_list('listing_id', flat=True)
    )
    cmp_ids = frozenset(
        UserCompareListing.objects.filter(user=user).values_list('listing_id', flat=True)
    )
    return {'favorite_listing_ids': fav, 'compare_listing_ids': cmp_ids}


class PropertyListingSerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    tags = PropertyTagSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    district = DistrictRefSerializer(read_only=True)
    highway = HighwayRefSerializer(read_only=True)
    is_favourite = serializers.SerializerMethodField()
    is_compare = serializers.SerializerMethodField()
    lat = serializers.DecimalField(
        source='latitude',
        max_digits=9,
        decimal_places=6,
        allow_null=True,
        read_only=True,
    )
    long = serializers.DecimalField(
        source='longitude',
        max_digits=9,
        decimal_places=6,
        allow_null=True,
        read_only=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request is not None and 'favorite_listing_ids' not in self.context:
            self.context.update(listing_favorite_compare_context(request))

    class Meta:
        model = PropertyListing
        fields = (
            'id',
            'code',
            'property_type',
            'name',
            'price',
            'settlement',
            'district',
            'highway',
            'address',
            'area',
            'land_area',
            'distance_to_mkad_km',
            'lat',
            'long',
            'has_asphalt_roads',
            'has_street_lighting',
            'has_guarded_territory',
            'near_shops',
            'near_school_kindergarten',
            'near_public_transport',
            'floors',
            'rooms',
            'bedrooms',
            'bathrooms',
            'year_built',
            'wall_material',
            'finishing',
            'electricity_supply',
            'water_supply',
            'sewage_type',
            'heating_type',
            'internet_connection',
            'communications',
            'description',
            'tags',
            'status',
            'status_display',
            'rejection_reason',
            'images',
            'created_at',
            'updated_at',
            'is_favourite',
            'is_compare',
        )
        read_only_fields = (
            'id',
            'code',
            'status',
            'rejection_reason',
            'created_at',
            'updated_at',
            'status_display',
            'images',
            'tags',
            'is_favourite',
            'is_compare',
            'lat',
            'long',
        )

    def get_is_favourite(self, obj) -> bool:
        ids = self.context.get('favorite_listing_ids')
        if not ids:
            return False
        return obj.pk in ids

    def get_is_compare(self, obj) -> bool:
        ids = self.context.get('compare_listing_ids')
        if not ids:
            return False
        return obj.pk in ids


class PropertyListingWriteSerializer(serializers.ModelSerializer):
    """Подписи в Swagger: «(русское имя) key» через label → title в OpenAPI."""

    lat = serializers.DecimalField(
        source='latitude',
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        label='(Широта WGS84) lat',
    )
    long = serializers.DecimalField(
        source='longitude',
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        label='(Долгота WGS84) long',
    )

    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source='district',
        required=False,
        allow_null=True,
        label='(Район, справочник) district_id',
        help_text='ID из `GET /api/v1/accounts/catalog/districts/` (справочник).',
    )
    highway_id = serializers.PrimaryKeyRelatedField(
        queryset=Highway.objects.all(),
        source='highway',
        required=False,
        allow_null=True,
        label='(Шоссе, справочник) highway_id',
        help_text='ID из `GET /api/v1/accounts/catalog/highways/`.',
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
        label='(Изображения) images',
        help_text='Файлы: повторяйте поле images для каждого файла (multipart).',
    )
    tags = serializers.JSONField(
        write_only=True,
        required=False,
        allow_null=True,
        label='(Теги) tags',
        help_text=(
            'JSON в теле: `["тег1","тег2"]` или `[{"id":1,"tag_name":"имя"}]`. '
            'В form-data: несколько полей `tags` **или** одна строка-состав `имя1,имя2` (разделитель запятая), '
            'либо одна JSON-строка с массивом. '
            'Для фильтров каталога используйте **точно** (строка в теге = имя чипа): '
            f'`{CATALOG_TAG_PROMO}`, `{CATALOG_TAG_START_SALES}`, `{CATALOG_TAG_FOREST}`, `{CATALOG_TAG_RAILWAY}` '
            '(соответствуют query `promo`, `start_sales`, `forest_access`, `near_railway`). '
            'Другие произвольные имена тоже допустимы.'
        ),
    )

    class Meta:
        model = PropertyListing
        fields = (
            'property_type',
            'name',
            'price',
            'settlement',
            'district_id',
            'highway_id',
            'address',
            'area',
            'land_area',
            'distance_to_mkad_km',
            'lat',
            'long',
            'has_asphalt_roads',
            'has_street_lighting',
            'has_guarded_territory',
            'near_shops',
            'near_school_kindergarten',
            'near_public_transport',
            'floors',
            'rooms',
            'bedrooms',
            'bathrooms',
            'year_built',
            'wall_material',
            'finishing',
            'electricity_supply',
            'water_supply',
            'sewage_type',
            'heating_type',
            'internet_connection',
            'communications',
            'description',
            'tags',
            'images',
        )
        extra_kwargs = {
            'property_type': {
                'label': '(Тип объекта) property_type',
                'help_text': 'land | house | apartment | commercial | other',
            },
            'name': {
                'label': '(Название) name',
            },
            'price': {
                'label': '(Цена, ₽) price',
                'help_text': 'Цена в рублях (число).',
            },
            'settlement': {'label': '(Населённый пункт) settlement'},
            'address': {
                'label': '(Адрес вручную) address',
                'help_text': 'Вручную: улица, дом (район/шоссе — только id справочников).',
            },
            'area': {
                'label': '(Площадь дома/объекта, м²) area',
                'help_text': 'м²; для участка без строения можно не указывать.',
            },
            'land_area': {
                'label': '(Площадь участка, сот.) land_area',
                'help_text': 'Земля в сотках.',
            },
            'distance_to_mkad_km': {
                'label': '(До МКАД, км) distance_to_mkad_km',
            },
            'has_asphalt_roads': {'label': '(Дороги асфальт) has_asphalt_roads'},
            'has_street_lighting': {'label': '(Освещение) has_street_lighting'},
            'has_guarded_territory': {'label': '(Охрана территории) has_guarded_territory'},
            'near_shops': {'label': '(Магазины рядом) near_shops'},
            'near_school_kindergarten': {'label': '(Школа/сад рядом) near_school_kindergarten'},
            'near_public_transport': {'label': '(ОТ рядом) near_public_transport'},
            'floors': {'label': '(Этажей) floors'},
            'rooms': {'label': '(Комнат) rooms'},
            'bedrooms': {'label': '(Спален) bedrooms'},
            'bathrooms': {'label': '(Санузлов) bathrooms'},
            'year_built': {'label': '(Год постройки) year_built'},
            'wall_material': {'label': '(Материал стен) wall_material'},
            'finishing': {'label': '(Отделка) finishing'},
            'electricity_supply': {'label': '(Электричество) electricity_supply'},
            'water_supply': {'label': '(Водоснабжение) water_supply'},
            'sewage_type': {'label': '(Канализация) sewage_type'},
            'heating_type': {'label': '(Отопление) heating_type'},
            'internet_connection': {'label': '(Интернет) internet_connection'},
            'communications': {
                'label': '(Коммуникации, кратко) communications',
                'help_text': 'Общая строка; детали — в отдельных полях выше.',
            },
            'description': {'label': '(Описание) description'},
        }

    def to_internal_value(self, data):
        request = self.context.get('request')
        mut = data.copy() if hasattr(data, 'copy') else dict(data)

        if request and getattr(request, 'FILES', None):
            files = request.FILES.getlist('images')
            if files:
                if hasattr(mut, 'setlist'):
                    mut.setlist('images', files)
                elif isinstance(mut, dict):
                    mut = {**mut, 'images': files}

        tags_coerced = None
        if request:
            rd = getattr(request, 'data', None)
            if rd is not None and hasattr(rd, 'getlist'):
                tl = rd.getlist('tags')
                if tl:
                    tags_coerced = coalesce_multipart_tags(tl)
            if tags_coerced is None and hasattr(request, 'POST'):
                tl = request.POST.getlist('tags')
                if tl:
                    tags_coerced = coalesce_multipart_tags(tl)
        if tags_coerced is None and 'tags' in mut:
            tags_coerced = mut.get('tags')

        if 'tags' in mut:
            del mut['tags']

        ret = super().to_internal_value(mut)
        if tags_coerced is not None:
            ret['tags'] = normalize_tags_input_to_sync(tags_coerced)
        return ret

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        tags_items = validated_data.pop('tags', None)
        validated_data['agent'] = self.context['request'].user
        validated_data.setdefault('status', PropertyListing.Status.MODERATION)
        obj = super().create(validated_data)
        if tags_items is not None:
            sync_property_tags(obj, tags_items)
        for i, img in enumerate(images):
            PropertyImage.objects.create(property=obj, image=img, sort_order=i)
        return obj

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)
        tags_items = validated_data.pop('tags', None)
        obj = super().update(instance, validated_data)
        if tags_items is not None:
            sync_property_tags(obj, tags_items)
        if images is not None:
            instance.images.all().delete()
            for i, img in enumerate(images):
                PropertyImage.objects.create(property=obj, image=img, sort_order=i)
        return obj


class PropertyListingUpdateSerializer(PropertyListingWriteSerializer):
    """PUT/PATCH: поля name и price не обязательны, если не меняете их."""

    class Meta(PropertyListingWriteSerializer.Meta):
        extra_kwargs = {
            **PropertyListingWriteSerializer.Meta.extra_kwargs,
            'name': {
                **PropertyListingWriteSerializer.Meta.extra_kwargs['name'],
                'required': False,
            },
            'price': {
                **PropertyListingWriteSerializer.Meta.extra_kwargs['price'],
                'required': False,
            },
        }


class PropertyTagsReplaceSerializer(serializers.Serializer):
    """Тело PUT /properties/{id}/tags/: тот же формат, что и tags при создании объекта."""

    tags = serializers.JSONField(
        help_text=(
            '`["а","б"]` или `[{"id":1,"tag_name":"х"}]`; `[]` удаляет все теги. '
            f'Чипы каталога (имена как в `tags`): `{CATALOG_TAG_PROMO}`, `{CATALOG_TAG_START_SALES}`, '
            f'`{CATALOG_TAG_FOREST}`, `{CATALOG_TAG_RAILWAY}`.'
        ),
    )
