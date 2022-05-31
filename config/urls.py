"""explorer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from scan.views.accounts import AccountsListView, AddressDetailView
from scan.views.assets import (
    AssetDetailView,
    AssetMintingDetailView,
    AssetDistributionDetailView,
    AssetHoldersListView,
    AssetListView,
    AssetTradesListView,
    AssetTransfersListView,
    
)
from scan.views.ats import AtDetailView, AtListView
from scan.views.blocks import BlockDetailView, BlockListView
from scan.views.index import index
from scan.views.marketplace import (
    MarketPlaceDetailView,
    MarketPlaceListView,
    MarketPlacePurchasesListView,
)
from scan.views.peers import (
    PeerMonitorDetailView,
    PeerMonitorListView,
    peers_charts_view,
)
from scan.views.pending_transactions import pending_transactions
from scan.views.search import search_view
from scan.views.transactions import TxDetailView, TxListView, tx_export_csv
from scan.views.cashbacks import CBListView
from scan.views.distribution import DistributionListView

urlpatterns = [
    path("", index, name="index"),
    path("distribution/", DistributionListView.as_view(), name="distribution"),
    path("cbs/", CBListView.as_view(), name="cbs"),
    path("blocks/", BlockListView.as_view(), name="blocks"),
    path("block/<str:height>", BlockDetailView.as_view(), name="block-detail"),
    path("txsPending/", pending_transactions, name="txs-pending"),
    path("txs/", TxListView.as_view(), name="txs"),
    path("tx/<str:id>", TxDetailView.as_view(), name="tx-detail"),
    path("accounts/", AccountsListView.as_view(), name="accounts"),
    path("address/<str:id>", AddressDetailView.as_view(), name="address-detail"),
    path("csv/<str:id>", tx_export_csv, name="account-csv"),
    path("asset/trades", AssetTradesListView.as_view(), name="asset-trades"),
    path("asset/transfers", AssetTransfersListView.as_view(), name="asset-transfers"),
    path("asset/holders", AssetHoldersListView.as_view(), name="asset-holders"),
    path("asset/mintings", AssetMintingDetailView.as_view(), name="asset-mintings"),
    path("asset/distributions", AssetDistributionDetailView.as_view(), name="asset-distributions"),
    path("assets/", AssetListView.as_view(), name="assets"),
    path("asset/<str:id>", AssetDetailView.as_view(), name="asset-detail"),
    path("mps/purchases", MarketPlacePurchasesListView.as_view(), name="mps-purchases"),
    path("mps/", MarketPlaceListView.as_view(), name="mps"),
    path("mp/<str:id>", MarketPlaceDetailView.as_view(), name="mp-detail"),
    path("ats/", AtListView.as_view(), name="ats"),
    path("at/<str:id>", AtDetailView.as_view(), name="at-detail"),
    path("search/", search_view, name="search"),
    path("peers/", PeerMonitorListView.as_view(), name="peers"),
    path("peers-charts/", peers_charts_view, name="peers-charts"),
    path("peer/<str:address>", PeerMonitorDetailView.as_view(), name="peer-detail"),
    # path("admin/", admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    urlpatterns = [path('django_query_profiler/', include('django_query_profiler.client.urls'))] + urlpatterns
