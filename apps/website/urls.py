from django.urls import path

from apps.website import views

app_name = 'website'

urlpatterns = [
    path('regions/', views.SiteRegionListView.as_view(), name='regions'),
    path('geo/', views.SiteGeoDetectAPIView.as_view(), name='geo-detect'),
    path('hero-slides/', views.HeroSlideListView.as_view(), name='hero-slides'),
    path('advantages/', views.AdvantageListView.as_view(), name='advantages'),
    path('services/', views.ServiceListView.as_view(), name='services'),
    path('services/<int:pk>/', views.ServiceDetailAPIView.as_view(), name='service-detail'),
    path('faq/', views.FAQListView.as_view(), name='faq'),
    path('articles/', views.BlogArticleListAPIView.as_view(), name='articles'),
    path('articles/<slug:slug>/', views.BlogArticleDetailAPIView.as_view(), name='article-detail'),
    path('team/', views.TeamListView.as_view(), name='team'),
    path('reviews/', views.ClientReviewListView.as_view(), name='reviews'),
    path('contacts/', views.SiteContactsView.as_view(), name='contacts'),
    path('consultation/', views.ConsultationCreateView.as_view(), name='consultation'),
]
