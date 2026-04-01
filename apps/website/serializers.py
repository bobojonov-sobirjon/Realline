from rest_framework import serializers

from apps.website.models import (
    AdvantageCard,
    Article,
    ClientReview,
    ConsultationLead,
    FAQEntry,
    HeroSlide,
    ServiceBenefitBlock,
    ServiceCard,
    ServiceFeatureLine,
    ServicePillTag,
    ServiceWorkflowStep,
    SiteContacts,
    SiteRegion,
    TeamMember,
)


class SiteRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteRegion
        fields = ('id', 'name', 'slug', 'sort_order', 'latitude', 'longitude')


class SiteGeoDetectSerializer(serializers.Serializer):
    """Ответ GET /site/geo/ — координаты и человекочитаемое название места."""

    client_ip = serializers.CharField()
    location_source = serializers.ChoiceField(choices=['coordinates', 'ip_demo'])
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    place_name = serializers.CharField(
        allow_null=True,
        required=False,
        help_text='Город / населённый пункт (Nominatim при lat/lon; при ip_demo — демо-город).',
    )
    full_address = serializers.CharField(allow_null=True, required=False)
    country_code = serializers.CharField(allow_null=True, required=False)


class HeroSlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSlide
        fields = ('id', 'title', 'subtitle', 'image', 'sort_order')


class AdvantageCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvantageCard
        fields = ('id', 'sort_order', 'title', 'body', 'image')


class ServiceCardSerializer(serializers.ModelSerializer):
    """Карточка для списка на главной / блок «Другие услуги»."""

    class Meta:
        model = ServiceCard
        fields = ('id', 'slug', 'sort_order', 'title', 'body', 'image')


class ServiceFeatureLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeatureLine
        fields = ('id', 'sort_order', 'text')


class ServicePillTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePillTag
        fields = ('id', 'sort_order', 'text')


class ServiceBenefitBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceBenefitBlock
        fields = ('id', 'sort_order', 'title', 'body')


class ServiceWorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceWorkflowStep
        fields = ('id', 'step_number', 'title', 'body')


class ServiceRelatedTeaserSerializer(serializers.ModelSerializer):
    """Другие услуги — без вложенных связей (без рекурсии)."""

    class Meta:
        model = ServiceCard
        fields = ('id', 'slug', 'sort_order', 'title', 'body', 'image')


class ServiceCardDetailSerializer(serializers.ModelSerializer):
    feature_lines = ServiceFeatureLineSerializer(many=True, read_only=True)
    pill_tags = ServicePillTagSerializer(many=True, read_only=True)
    benefit_blocks = ServiceBenefitBlockSerializer(many=True, read_only=True)
    workflow_steps = ServiceWorkflowStepSerializer(many=True, read_only=True)
    related_services = ServiceRelatedTeaserSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceCard
        fields = (
            'id',
            'slug',
            'sort_order',
            'title',
            'body',
            'hero_text',
            'image',
            'section_features_title',
            'section_workflow_title',
            'cta_label',
            'feature_lines',
            'pill_tags',
            'benefit_blocks',
            'workflow_steps',
            'related_services',
        )


class FAQEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQEntry
        fields = ('id', 'sort_order', 'question', 'answer')


class ArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ('id', 'slug', 'title', 'lead', 'description', 'image', 'published_at')


class ArticleDetailSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            'id',
            'slug',
            'title',
            'lead',
            'description',
            'image',
            'published_at',
            'sections',
            'body',
        )

    def get_sections(self, obj):
        out = []
        for sec in obj.content_sections.all():
            out.append(
                {
                    'title': sec.title,
                    'intro': sec.intro or '',
                    'list_title': sec.list_title or '',
                    'items': [it.text for it in sec.list_items.all()],
                    'closing': sec.closing or '',
                }
            )
        return out


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ('id', 'sort_order', 'full_name', 'role', 'experience', 'photo')


class ClientReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientReview
        fields = ('id', 'sort_order', 'author_name', 'city', 'text')


class SiteContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteContacts
        fields = (
            'phone',
            'email',
            'address',
            'work_hours',
            'telegram_url',
            'vk_url',
            'map_embed_url',
        )


class ConsultationLeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationLead
        fields = ('name', 'phone', 'email', 'message', 'personal_data_consent')

    def validate_personal_data_consent(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо согласие на обработку персональных данных.')
        return value
