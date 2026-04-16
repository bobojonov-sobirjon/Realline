import django_filters
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.website.models import (
    AdvantageCard,
    Article,
    ArticleSection,
    ArticleSectionItem,
    ClientReview,
    ConsultationLead,
    FAQEntry,
    HeroSlide,
    ServiceCard,
    SiteContacts,
    SiteRegion,
    TeamMember,
)
from apps.website.geo_utils import fake_ip_geolocation_demo, get_client_ip, reverse_geocode_osm
from apps.website.serializers import (
    AdvantageCardSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    ClientReviewSerializer,
    ConsultationLeadCreateSerializer,
    FAQEntrySerializer,
    HeroSlideSerializer,
    ServiceCardDetailSerializer,
    ServiceCardSerializer,
    SiteContactsSerializer,
    SiteGeoDetectSerializer,
    SiteRegionSerializer,
    TeamMemberSerializer,
)


_PUB = (
    '**Доступ:** публично, **без JWT**. Все тексты, изображения и порядок записей настраиваются в **админ-панели Django** '
    '(приложение сайта). Неактивные записи (`is_active=False` и аналоги) в выдачу не попадают там, где это предусмотрено моделью.'
)


@extend_schema(
    tags=['Сайт — регионы'],
    summary='Регионы / города (шапка сайта)',
    description=(
        _PUB
        + '\n\n**Назначение:** регионы/города для переключателя в шапке лендинга.\n\n'
        + '**Query-параметры (опционально):** **`name`** или **`search`** — одно и то же: оставить только регионы, '
        'в названии которых встречается подстрока (**без учёта регистра**). Если переданы оба, используется **`name`**.'
    ),
    parameters=[
        OpenApiParameter(
            name='name',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Подстрока для поиска в названии города/региона (регистр не важен).',
        ),
        OpenApiParameter(
            name='search',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Синоним `name`; при одновременной передаче приоритет у параметра `name`.',
        ),
    ],
    responses={200: SiteRegionSerializer(many=True)},
)
class SiteRegionListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = SiteRegion.objects.filter(is_active=True)
        q = (request.query_params.get('name') or request.query_params.get('search') or '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return Response(SiteRegionSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — регионы'],
    summary='Геолокация: название места по координатам или демо по IP',
    description=(
        _PUB
        + '\n\n**Назначение:** подставить человекочитаемое название места для виджета «ваш регион».\n\n'
        '- **Пара `lat` + `lon`:** обратное геокодирование через **OpenStreetMap Nominatim**; в ответе '
        '`place_name`, `full_address`, `country_code`. Требуется исходящий интернет с сервера.\n'
        '- **Без координат:** демонстрационный режим — координаты генерируются от IP, подпись города фиктивная (РФ).\n\n'
        'Справочник **`SiteRegion`** этим методом **не читается** — только внешняя геослужба или демо.'
    ),
    parameters=[
        OpenApiParameter(
            name='lat',
            type=float,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Широта WGS84 (вместе с `lon`).',
        ),
        OpenApiParameter(
            name='lon',
            type=float,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Долгота WGS84 (вместе с `lat`).',
        ),
    ],
    responses={200: SiteGeoDetectSerializer, 400: OpenApiResponse(description='Некорректные lat/lon')},
)
class SiteGeoDetectAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        ip = get_client_ip(request)
        lat_q = request.query_params.get('lat')
        lon_q = request.query_params.get('lon')
        ip_geolocation = None
        if lat_q is not None and lon_q is not None:
            if lat_q == '' or lon_q == '':
                return Response({'detail': 'Передайте оба параметра lat и lon или ни одного.'}, status=400)
            try:
                lat_f = float(lat_q)
                lon_f = float(lon_q)
            except (TypeError, ValueError):
                return Response({'detail': 'lat и lon должны быть числами.'}, status=400)
            source = 'coordinates'
        elif lat_q is not None or lon_q is not None:
            return Response({'detail': 'Укажите и lat, и lon одновременно.'}, status=400)
        else:
            ip_geolocation = fake_ip_geolocation_demo(ip)
            lat_f = float(ip_geolocation['latitude'])
            lon_f = float(ip_geolocation['longitude'])
            source = 'ip_demo'

        place_name = None
        full_address = None
        country_code = None
        if source == 'coordinates':
            geo = reverse_geocode_osm(lat_f, lon_f)
            if geo:
                place_name = geo.get('place_name')
                full_address = geo.get('full_address')
                country_code = geo.get('country_code')
        else:
            place_name = ip_geolocation.get('city_name')
            full_address = f"{ip_geolocation['city_name']}, {ip_geolocation['country_name']}"
            country_code = ip_geolocation.get('country_code')

        data = {
            'client_ip': ip,
            'location_source': source,
            'latitude': lat_f,
            'longitude': lon_f,
            'place_name': place_name,
            'full_address': full_address,
            'country_code': country_code,
        }
        return Response(data)


@extend_schema(
    tags=['Сайт — баннеры'],
    summary='Слайды / баннеры главной',
    description=(
        _PUB
        + '\n\n**Назначение:** элементы карусели / hero-блока на главной (изображение, заголовок, ссылка и т.д.).\n\n'
        + '**Фильтр (опционально):** `site_region` (ID) или `site_region_slug` (slug) — '
        + 'оставить слайды для конкретного региона. '
        + 'Если нужно добавить «общие» слайды (где регион не задан) — передайте `include_global=1`.\n'
        + 'Если переданы оба (`site_region` и `site_region_slug`) — приоритет у `site_region`.'
    ),
    parameters=[
        OpenApiParameter(
            name='site_region',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='ID региона (`SiteRegion.id`).',
        ),
        OpenApiParameter(
            name='site_region_slug',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Slug региона (`SiteRegion.slug`). По умолчанию возвращаются только слайды этого региона.',
        ),
        OpenApiParameter(
            name='include_global',
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Если `1`, то вместе с региональными вернуть и «общие» слайды (где `site_region` не задан).',
        ),
    ],
    responses={200: HeroSlideSerializer(many=True)},
)
class HeroSlideListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = HeroSlide.objects.filter(is_active=True)
        filterset = HeroSlideFilter(request.query_params, queryset=qs)
        if not filterset.is_valid():
            return Response(
                {'detail': 'Filter parametrlari notogri.', 'errors': filterset.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = filterset.qs
        if not request.query_params.get('site_region') and not request.query_params.get('site_region_slug'):
            qs = qs.filter(site_region__isnull=True)

        serializer = HeroSlideSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class HeroSlideFilter(django_filters.FilterSet):
    site_region = django_filters.NumberFilter(field_name='site_region_id')
    site_region_slug = django_filters.CharFilter(field_name='site_region__slug', lookup_expr='iexact')

    class Meta:
        model = HeroSlide
        fields = ('site_region', 'site_region_slug')


@extend_schema(
    tags=['Сайт — преимущества'],
    summary='Преимущества («Почему мы»)',
    description=_PUB + '\n\n**Назначение:** карточки преимуществ компании (иконка, заголовок, краткий текст).',
    responses={200: AdvantageCardSerializer(many=True)},
)
class AdvantageListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = AdvantageCard.objects.filter(is_active=True)
        return Response(AdvantageCardSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — услуги'],
    summary='Дополнительные услуги',
    description=_PUB + '\n\n**Назначение:** краткий список услуг для блока на главной (без полного лендинга услуги).',
    responses={200: ServiceCardSerializer(many=True)},
)
class ServiceListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = ServiceCard.objects.filter(is_active=True)
        return Response(ServiceCardSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — услуги'],
    summary='Услуга: полная страница по id',
    description=(
        _PUB
        + '\n\n**Назначение:** полная страница одной услуги по **id**: hero, блок «Что вы получите», чипы, '
        'блоки выгод, шаги процесса, превью связанных услуг. Крошки на фронте: Главная → Услуги → заголовок.'
    ),
    responses={
        200: ServiceCardDetailSerializer,
        404: OpenApiResponse(description='Не найдена или снята с публикации'),
    },
)
class ServiceDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request, pk):
        active_services = ServiceCard.objects.filter(is_active=True).order_by('sort_order', 'id')
        service = get_object_or_404(
            ServiceCard.objects.filter(is_active=True).prefetch_related(
                'feature_lines',
                'pill_tags',
                'benefit_blocks',
                'workflow_steps',
                Prefetch('related_services', queryset=active_services),
            ),
            pk=pk,
        )
        return Response(ServiceCardDetailSerializer(service, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — FAQ'],
    summary='FAQ (вопрос — ответ)',
    description=_PUB + '\n\n**Назначение:** пары вопрос–ответ для блока FAQ (порядок как в админке).',
    responses={200: FAQEntrySerializer(many=True)},
)
class FAQListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = FAQEntry.objects.filter(is_active=True)
        return Response(FAQEntrySerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — блог'],
    summary='Статьи блога (список)',
    description=_PUB + '\n\n**Назначение:** анонсы опубликованных статей (без длинного `body`; полный контент — в детали по **slug**).',
    responses={200: ArticleListSerializer(many=True)},
)
class BlogArticleListAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = Article.objects.filter(is_published=True)
        return Response(ArticleListSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — блог'],
    summary='Статья блога (деталь по slug)',
    description=_PUB + '\n\n**Назначение:** одна статья по **slug** URL; основной контент в **`sections`** (блоки со списками); '
    'поле **`body`** может использоваться для старых записей.',
    responses={200: ArticleDetailSerializer},
)
class BlogArticleDetailAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request, slug):
        section_qs = ArticleSection.objects.order_by('sort_order', 'id').prefetch_related(
            Prefetch(
                'list_items',
                queryset=ArticleSectionItem.objects.order_by('sort_order', 'id'),
            )
        )
        qs = Article.objects.filter(is_published=True).prefetch_related(
            Prefetch('content_sections', queryset=section_qs)
        )
        article = get_object_or_404(qs, slug=slug)
        return Response(ArticleDetailSerializer(article, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — команда'],
    summary='Команда',
    description=_PUB + '\n\n**Назначение:** карточки сотрудников (ФИО, должность, фото, краткий текст).',
    responses={200: TeamMemberSerializer(many=True)},
)
class TeamListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = TeamMember.objects.filter(is_active=True)
        return Response(TeamMemberSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — отзывы'],
    summary='Отзывы клиентов',
    description=_PUB + '\n\n**Назначение:** опубликованные отзывы для страницы «Отзывы» (автор, текст, рейтинг при наличии в модели).',
    responses={200: ClientReviewSerializer(many=True)},
)
class ClientReviewListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        qs = ClientReview.objects.filter(is_published=True)
        return Response(ClientReviewSerializer(qs, many=True, context={'request': request}).data)


@extend_schema(
    tags=['Сайт — контакты'],
    summary='Контакты компании',
    description=_PUB + '\n\n**Назначение:** единая карточка контактов (телефон, email, адрес, соцсети, часы работы). '
    'В базе хранится одна активная запись; если не создана — **404**.',
    responses={
        200: SiteContactsSerializer,
        404: OpenApiResponse(description='Запись контактов ещё не создана'),
    },
)
class SiteContactsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request):
        row = SiteContacts.objects.order_by('pk').first()
        if not row:
            return Response({'detail': 'Контакты не настроены.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SiteContactsSerializer(row, context={'request': request}).data)


_ConsultationCreated = inline_serializer(
    name='ConsultationLeadCreated',
    fields={
        'id': serializers.IntegerField(help_text='ID созданной заявки'),
        'detail': serializers.CharField(),
    },
)


@extend_schema(
    tags=['Сайт — консультации'],
    summary='Заявка «Получить консультацию»',
    description=(
        _PUB
        + '\n\n**Назначение:** форма обратной связи с лендинга; создаётся запись **ConsultationLead** для менеджеров.\n\n'
        + '**Обязательно:** согласие на обработку персональных данных (**`personal_data_consent` = true**). '
        + 'Имя, телефон, email и сообщение — по схеме сериализатора.\n\n'
        + '**Ответ:** **201**, `id` заявки и короткий текст успеха.'
    ),
    request=ConsultationLeadCreateSerializer,
    responses={201: _ConsultationCreated},
)
class ConsultationCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def post(self, request):
        ser = ConsultationLeadCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj: ConsultationLead = ser.save()
        return Response({'id': obj.pk, 'detail': 'Заявка принята.'}, status=status.HTTP_201_CREATED)
