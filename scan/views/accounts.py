from django.db.models import Q
from django.views.generic import ListView

from java_wallet.models import (
    Account,
    AccountAsset,
    AssetTransfer,
    Block,
    IndirecIncoming,
    Trade,
    Transaction,
)
from scan.caching_paginator import CachingPaginator
from scan.helpers.queries import (
    get_account_name,
    get_asset_details,
    get_pool_id_for_account,
    get_pool_id_for_block,
    get_total_accounts_count,
    get_total_circulating,
)
from scan.views.assets import fill_data_asset_trade, fill_data_asset_transfer
from scan.views.base import IntSlugDetailView
from scan.views.transactions import fill_data_transaction


class AccountsListView(ListView):
    model = Account
    queryset = (
        Account.objects.using("java_wallet").filter(latest=True,balance__gte=10000000000000)
            .exclude(id=0).all()
    )
    template_name = "accounts/list.html"
    context_object_name = "accounts"
    paginator_class = CachingPaginator
    paginate_by = 25
    ordering = "-balance"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs[:1000]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["balance__sum"] = get_total_circulating()
        context["accounts_cnt"] = get_total_accounts_count()
        return context


class AddressDetailView(IntSlugDetailView):
    model = Account
    queryset = Account.objects.using("java_wallet").filter(latest=True).all()
    template_name = "accounts/detail.html"
    context_object_name = "address"
    slug_field = "id"
    slug_url_kwarg = "id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]

        if obj.id == 0:
            obj.name = "Burn Address";

        # To also show contract names when checking as an account
        if not obj.name:
            obj.name = get_account_name(obj.id)

        # transactions
        indirects = (
            IndirecIncoming.objects.using("java_wallet")
            .values_list('transaction_id', flat=True)
            .filter(account_id=obj.id)
        )

        txs_cnt = (
            Transaction.objects.using("java_wallet")
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id))
            .count() + indirects.count()
        )
        txs = (
            Transaction.objects.using("java_wallet")
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id) | Q(id__in=indirects))
            .order_by("-height")[:min(txs_cnt, 15)]
        )

        for t in txs:
            fill_data_transaction(t, list_page=True)

        context["txs"] = txs
        context["txs_cnt"] = txs_cnt

        # assets

        assets_cnt = (
            AccountAsset.objects.using("java_wallet")
            .filter(account_id=obj.id, latest=True)
            .count()
        )
        assets = (
            AccountAsset.objects.using("java_wallet")
            .filter(account_id=obj.id, latest=True)
            .order_by("-db_id")[:assets_cnt]
        )

        for asset in assets:
            asset.name, asset.decimals, asset.total_quantity, asset.mintable = get_asset_details(
                asset.asset_id
            )

        context["assets"] = assets
        context["assets_cnt"] = assets_cnt

        # assets transfer

        assets_transfers_cnt = (
            AssetTransfer.objects.using("java_wallet")
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id))
            .count()
        )
        assets_transfers = (
            AssetTransfer.objects.using("java_wallet")
            .using("java_wallet")
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id))
            .order_by("-height")[:min(assets_transfers_cnt, 15)]
        )

        for transfer in assets_transfers:
            fill_data_asset_transfer(transfer)

        context["assets_transfers"] = assets_transfers
        context["assets_transfers_cnt"] = assets_transfers_cnt

        # assets trades

        assets_trades_cnt = (
            Trade.objects.using("java_wallet")
            .filter(Q(buyer_id=obj.id) | Q(seller_id=obj.id))
            .count()
        )
        assets_trades = (
            Trade.objects.using("java_wallet")
            .using("java_wallet")
            .filter(Q(buyer_id=obj.id) | Q(seller_id=obj.id))
            .order_by("-height")[:min(assets_trades_cnt, 15)]
        )

        for trade in assets_trades:
            fill_data_asset_trade(trade)

        context["assets_trades"] = assets_trades
        context["assets_trades_cnt"] = assets_trades_cnt

        # pool info

        pool_id = get_pool_id_for_account(obj.id)
        if pool_id:
            obj.pool_id = pool_id
            obj.pool_name = get_account_name(pool_id)

        # blocks

        mined_blocks = (
            Block.objects.using("java_wallet")
            .filter(generator_id=obj.id)
            .order_by("-height")[:15]
        )

        for block in mined_blocks:
            pool_id = get_pool_id_for_block(block)
            if pool_id:
                block.pool_id = pool_id
                block.pool_name = get_account_name(pool_id)

        context["mined_blocks"] = mined_blocks
        context["mined_blocks_cnt"] = (
            Block.objects.using("java_wallet").filter(generator_id=obj.id).count()
        )

        return context
