from datetime import datetime
import os
import simplejson as json

from django.db.models import Q
from django.http import Http404
from django.views.generic import ListView
from config.settings import BLOCKED_ASSETS, PHISHING_ASSETS, FEATURED_ASSETS

from java_wallet.models import Asset, AssetTransfer, Trade
from scan.caching_paginator import CachingPaginator
from scan.helpers.queries import get_account_name, get_asset_details
from scan.templatetags.burst_tags import burst_amount, mul_decimals
from scan.views.base import IntSlugDetailView
from scan.views.filters.assets import AssetTransferFilter, TradeFilter


def fill_data_asset_transfer(transfer):
    transfer.name, transfer.decimals, transfer.total_quantity, mintable = get_asset_details(
        transfer.asset_id
    )
    transfer.sender_name = get_account_name(transfer.sender_id)
    transfer.recipient_name = get_account_name(transfer.recipient_id)


def fill_data_asset_trade(trade):
    trade.name, trade.decimals, trade.total_quantity, mintable = get_asset_details(trade.asset_id)
    trade.buyer_name = get_account_name(trade.buyer_id)
    trade.seller_name = get_account_name(trade.seller_id)


class AssetListView(ListView):
    model = Asset
    queryset = Asset.objects.using("java_wallet").all()
    template_name = "assets/list.html"
    context_object_name = "assets"
    paginator_class = CachingPaginator
    paginate_by = 25
    ordering = "-height"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]

        context["BLOCKED_ASSETS"] = BLOCKED_ASSETS
        context["PHISHING_ASSETS"] = PHISHING_ASSETS

        for t in obj:
            t.account_name = get_account_name(t.account_id)
            t.name = t.name.upper()
            if t.name in BLOCKED_ASSETS or t.name in PHISHING_ASSETS:
                t.name = str(t.id)[0:10]

        if FEATURED_ASSETS:
            featured_assets = Asset.objects.using("java_wallet").filter(id__in=list(map(int, FEATURED_ASSETS)))
            context["featured_assets"] = featured_assets
            for t in featured_assets:
                t.account_name = get_account_name(t.account_id)

        return context


class AssetTradesListView(ListView):
    model = Trade
    queryset = Trade.objects.using("java_wallet").all()
    template_name = "assets/trades.html"
    context_object_name = "assets_trades"
    paginator_class = CachingPaginator
    paginate_by = 25
    ordering = "-height"
    filter_set = None

    def get_queryset(self):
        self.filter_set = TradeFilter(self.request.GET, queryset=super().get_queryset())
        if self.filter_set.is_valid() and self.filter_set.data:
            qs = self.filter_set.qs[:10000]
        else:
            raise Http404()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assets_trades_cnt"] = self.filter_set.qs.count()
        obj = context[self.context_object_name]

        for trade in obj:
            fill_data_asset_trade(trade)

        return context


class AssetTransfersListView(ListView):
    model = AssetTransfer
    queryset = AssetTransfer.objects.using("java_wallet").all()
    template_name = "assets/transfers.html"
    context_object_name = "assets_transfers"
    paginator_class = CachingPaginator
    paginate_by = 25
    ordering = "-height"
    filter_set = None

    def get_queryset(self):
        self.filter_set = AssetTransferFilter(
            self.request.GET, queryset=super().get_queryset()
        )
        if self.filter_set.is_valid() and self.filter_set.data:
            qs = self.filter_set.qs[:10000]
        else:
            raise Http404()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assets_transfers_cnt"] = self.filter_set.qs.count()
        obj = context[self.context_object_name]
        for transfer in obj:
            fill_data_asset_transfer(transfer)

        return context


class AssetDetailView(IntSlugDetailView):
    model = Asset
    queryset = Asset.objects.using("java_wallet").all()
    template_name = "assets/detail.html"
    context_object_name = "asset"
    slug_field = "id"
    slug_url_kwarg = "id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]
        obj.account_name = get_account_name(obj.account_id)

        name, decimals, total_quantity, mintable = get_asset_details(obj.id)

        # assets transfer

        assets_transfers = (
            AssetTransfer.objects.using("java_wallet")
            .using("java_wallet")
            .filter(asset_id=obj.id)
            .order_by("-height")[:15]
        )

        for transfer in assets_transfers:
            fill_data_asset_transfer(transfer)

        context["assets_transfers"] = assets_transfers
        context["assets_transfers_cnt"] = (
            AssetTransfer.objects.using("java_wallet").filter(asset_id=obj.id).count()
        )

        # assets trades

        assets_trades = (
            Trade.objects.using("java_wallet")
            .using("java_wallet")
            .filter(asset_id=obj.id)
            .order_by("-height")[:15]
        )

        for trade in assets_trades:
            fill_data_asset_trade(trade)

        context["assets_trades"] = assets_trades
        context["assets_trades_cnt"] = (
            Trade.objects.using("java_wallet").filter(asset_id=obj.id).count()
        )


        # price history

        price_query = (
            Trade.objects.using("java_wallet")
            .using("java_wallet")
            .filter(asset_id=obj.id)
            .order_by("-height")[:2000]
        )

        price_history = "[\n"
        old_time = None
        last_price = None
        now = datetime.now().strftime("%Y-%m-%d")
        for trade in reversed(price_query):
            price = burst_amount(mul_decimals(trade.price, decimals))
            time = trade.timestamp.strftime("%Y-%m-%d")
            last_price = price
            if time != old_time and time != now:
                # one per day
                price_history += "{ time: '" + time + "', value: " + str(price) + " },\n"
                old_time = time
        
        # add now as latest price
        if last_price:
            price_history += "{ time: '" + now + "', value: " + str(last_price) + " },\n"

        price_history += "]"

        context["price_history"] = price_history

        return context
