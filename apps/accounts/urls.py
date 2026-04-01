from django.urls import path

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('catalog/properties/', views.PropertyCatalogListView.as_view(), name='property-catalog'),
    path('catalog/districts/', views.DistrictListView.as_view(), name='catalog-districts'),
    path('catalog/highways/', views.HighwayListView.as_view(), name='catalog-highways'),
    path('register/', views.AgentRegisterApplicationView.as_view(), name='register'),
    path('login/', views.AgentTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', views.AgentTokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.AgentProfileRetrieveUpdateView.as_view(), name='profile'),
    path('profile/favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('profile/favorites/add/', views.FavoriteAddView.as_view(), name='favorite-add'),
    path(
        'profile/favorites/<int:listing_id>/',
        views.FavoriteRemoveView.as_view(),
        name='favorite-remove',
    ),
    path('profile/compare/', views.CompareListView.as_view(), name='compare-list'),
    path('profile/compare/add/', views.CompareAddView.as_view(), name='compare-add'),
    path(
        'profile/compare/<int:listing_id>/',
        views.CompareRemoveView.as_view(),
        name='compare-remove',
    ),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('properties/', views.PropertyListingListCreateView.as_view(), name='property-list-create'),
    path('properties/<int:pk>/tags/', views.PropertyTagsReplaceView.as_view(), name='property-tags-replace'),
    path('properties/<int:pk>/', views.PropertyListingDetailView.as_view(), name='property-detail'),
    path('properties/<int:pk>/unpublish/', views.PropertyUnpublishView.as_view(), name='property-unpublish'),
    path('properties/<int:pk>/resubmit/', views.PropertyResubmitView.as_view(), name='property-resubmit'),
]
