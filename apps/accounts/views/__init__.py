from apps.accounts.views.auth import (
    AgentRegisterApplicationView,
    AgentTokenObtainPairView,
    AgentTokenRefreshView,
)
from apps.accounts.views.catalog import (
    DistrictListView,
    HighwayListView,
    PropertyCatalogDetailView,
    PropertyCatalogListView,
    PropertyCategoryListView,
    PropertyListingUnitListView,
    PropertyListingUnitSummaryView,
    PropertyPublishedDetailView,
    PropertyPublishedListView,
)
from apps.accounts.views.favorites_compare import (
    CompareAddView,
    CompareListView,
    CompareRemoveView,
    FavoriteAddView,
    FavoriteListView,
    FavoriteRemoveView,
)
from apps.accounts.views.profile import AgentProfileRetrieveUpdateView, ChangePasswordView
from apps.accounts.views.listing_rejections import (
    PropertyListingRejectionNoticeDetailView,
    PropertyListingRejectionNoticeListView,
)
from apps.accounts.views.properties import (
    PropertyListingDetailView,
    PropertyListingListCreateView,
    PropertyResubmitView,
    PropertyTagsReplaceView,
    PropertyUnpublishView,
)

__all__ = (
    'AgentProfileRetrieveUpdateView',
    'AgentRegisterApplicationView',
    'AgentTokenObtainPairView',
    'AgentTokenRefreshView',
    'ChangePasswordView',
    'CompareAddView',
    'CompareListView',
    'CompareRemoveView',
    'DistrictListView',
    'FavoriteAddView',
    'FavoriteListView',
    'FavoriteRemoveView',
    'HighwayListView',
    'PropertyCatalogDetailView',
    'PropertyCatalogListView',
    'PropertyListingUnitListView',
    'PropertyListingUnitSummaryView',
    'PropertyPublishedDetailView',
    'PropertyPublishedListView',
    'PropertyCategoryListView',
    'PropertyListingDetailView',
    'PropertyListingListCreateView',
    'PropertyListingRejectionNoticeDetailView',
    'PropertyListingRejectionNoticeListView',
    'PropertyResubmitView',
    'PropertyTagsReplaceView',
    'PropertyUnpublishView',
)
