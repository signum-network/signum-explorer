from django.db.models import Q, F, Count
from django.views.generic import ListView

from java_wallet.models import (
    Account,
    AccountBalance,
    AccountAsset,
    Alias,
    Subscription,
    AssetTransfer,
    At,
    Block,
    IndirecIncoming,
    Trade,
    Transaction,
)
from scan.caching_paginator import CachingPaginator
from scan.helpers.queries import (
    get_account_name,
    get_asset_details_owner,
    get_pool_id_for_account,
    get_pool_id_for_block,
    get_total_accounts_count,
    get_total_circulating,
    check_is_contract,
)
from scan.views.assets import fill_data_asset_trade, fill_data_asset_transfer
from scan.views.base import IntSlugDetailView
from scan.views.transactions import fill_data_transaction
from scan.templatetags.burst_tags import cashback_amount

from config.settings import DEBUG
if DEBUG:
    from silk.profiling.profiler import silk_profile

#from scan.views.miners import get_miners

class AccountsListView(ListView):
    model = Account
    queryset = (
        AccountBalance.objects.using("java_wallet").filter(latest=True,balance__gte=10000000000000).exclude(id=0).all()
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

    #@silk_profile(name='Detailed Account View')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]
        
        # To also show contract names when checking as an account
        if not obj.name:
            obj.name = get_account_name(obj.id)

        obj.is_contract = check_is_contract(obj.id)
        
        # Transactions p1
        txs_db = (
            Transaction.objects
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id))
            .prefetch_related("sender_id__recipient_id__cash_back_id__height__id")
        )

        # cashback ##Calling QuerySet.filter() after union() is not supported##
        if obj.id == 0:
            cbs = 0
            cbs_cnt = 0
            total_cashback = 0 
        else:
            cash_query = txs_db.filter(Q(cash_back_id=obj.id))
            cbs_cnt = cash_query.count()
            cbs = cash_query.order_by("-height")[:min(cbs_cnt, 15)]
            total_cashback = 0 
            for cb in cash_query:
                total_cashback += cashback_amount(cb.fee)
        context["total_cashback"] = total_cashback
        context["cbs"] = cbs
        context["cbs_cnt"] = cbs_cnt

        # Transactions p2
        indirects_query = (
            IndirecIncoming.objects.using("java_wallet")
            .values_list('transaction_id', flat=True)
            .filter(account_id=obj.id)
        )
        indirects_count = indirects_query.count()
        if indirects_count > 0:
            txs_indirects = txs_db.filter(id__in=indirects_query)
            txs_db = txs_db.union(txs_indirects)
        txs_cnt = txs_db.count()# + indirects_count
        txs = txs_db.order_by("-height")[:min(txs_cnt, 15)]
        for t in txs:
            fill_data_transaction(t, list_page=True)
        context["txs"] = txs
        context["txs_cnt"] = txs_cnt

        # aliases
        alias_query = (
            Alias.objects.using("java_wallet")
            .filter(account_id=obj.id, latest=True)
            .order_by("alias_name")
        )
        alias_cnt = alias_query.count()
        aliases = alias_query
        context["aliases"] = aliases[:min(alias_cnt, 25)]
        context["alias_cnt"] = alias_cnt

        # subscriptions
        subscription_query = (
            Subscription.objects.using("java_wallet")
            .filter(sender_id=obj.id, latest=True)
            .order_by("-height")
        )
        subscription_cnt = subscription_query.count()
        subscriptions = subscription_query
        context["subscriptions"] = subscriptions[:min(subscription_cnt, 25)]
        context["subscription_cnt"] = subscription_cnt

        # assets
        asset_database = (
            AccountAsset.objects
            .filter(account_id=obj.id, latest=True)
            .prefetch_related("account_id__db_id")
        )
        assets_cnt = asset_database.count()
        assets = asset_database.order_by("-db_id")[:min(assets_cnt, 15)]
        for asset in assets:
            asset.name, asset.decimals, asset.total_quantity, asset.mintable, asset.owner_id = get_asset_details_owner(asset.asset_id)
        context["assets"] = assets
        context["assets_cnt"] = assets_cnt

        # assets transfer
        asset_transfer_db = (
            AssetTransfer.objects.using("java_wallet")
            .filter(Q(sender_id=obj.id) | Q(recipient_id=obj.id))
            .prefetch_related("sender_id__recipient_id__height")
        )
        assets_transfers_cnt= asset_transfer_db.count()
        assets_transfers = asset_transfer_db.order_by("-height")[:min(assets_transfers_cnt, 15)]
        for transfer in assets_transfers:
            fill_data_asset_transfer(transfer)
        context["assets_transfers"] = assets_transfers
        context["assets_transfers_cnt"] = assets_transfers_cnt

        # assets trades
        trades_db = (
            Trade.objects.using("java_wallet")
            .filter(Q(buyer_id=obj.id) | Q(seller_id=obj.id))
            .prefetch_related("buyer_id__seller_id__height")
        )
        assets_trades_cnt = trades_db.count()
        assets_trades = trades_db.order_by("-height")[:min(assets_trades_cnt, 15)]
        for trade in assets_trades:
            fill_data_asset_trade(trade)
        context["assets_trades"] = assets_trades
        context["assets_trades_cnt"] = assets_trades_cnt
        
        # pool info
        pool_id = get_pool_id_for_account(obj.id)
        if pool_id:
            obj.pool_id = pool_id
            obj.pool_name = get_account_name(pool_id)

        # ats
        ats_db = (
            At.objects.using("java_wallet")
            .filter(creator_id=obj.id)
            .prefetch_related("creator_id__height__creator_name")
        )
        ats_cnt = ats_db.count()
        ats = ats_db.order_by("-height")[:min(ats_cnt, 15)]
        for at in ats:
            at.creator_name = get_account_name(obj.id)
        context["ats"] = ats
        context["ats_cnt"] = ats_cnt
        
        # blocks
        
        blocks_db = (
            Block.objects.using("java_wallet")
            .filter(generator_id=obj.id)
            .prefetch_related("generator_id__height")
        )
        mined_blocks_cnt = blocks_db.count()
        mined_blocks = blocks_db.order_by("-height")[:min(mined_blocks_cnt, 15)]
        for block in mined_blocks:
            pool_id = get_pool_id_for_block(block)
            if pool_id:
                block.pool_id = pool_id
                block.pool_name = get_account_name(pool_id)
        context["mined_blocks"] = mined_blocks
        context["mined_blocks_cnt"] = mined_blocks_cnt
        
        # miners
        #miners = get_miners(obj.id)
        #context["miners"] = miners

        #miners_cnt = len(miners)
        #context["miners_cnt"] = miners_cnt

        return context
