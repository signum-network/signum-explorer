import time
import os

from datetime import datetime
from django.conf import settings

from django.db.models import Sum

from cache_memoize import cache_memoize
from burst.api.brs.v1.api import BrsApi
from burst.constants import BLOCK_CHAIN_START_AT, TxSubtypeBurstMining, TxType
from java_wallet.fields import get_desc_tx_type

from java_wallet.models import Account, Asset, Block, RewardRecipAssign, Transaction


@cache_memoize(3600)
def get_account_name(account_id: int) -> str:
    if account_id == 0:
        return "Burn Address"
    return (
        Account.objects.using("java_wallet")
        .filter(id=account_id, latest=True)
        .values_list("name", flat=True)
        .first()
    )


@cache_memoize(None)
def get_asset_details(asset_id: int) -> (str, int, int, bool):
    version = os.environ.get('BRS_P2P_VERSION')

    if version.startswith('3.3'):
        asset_details = (
            Asset.objects.using("java_wallet")
            .filter(id=asset_id)
            .values_list("name", "decimals", "quantity", "mintable")
            .first()
        )
    else:
        asset_details = (
            Asset.objects.using("java_wallet")
            .filter(id=asset_id)
            .values_list("name", "decimals", "quantity")
            .first()
        )
        asset_details += (False,)

    return asset_details


@cache_memoize(None)
def get_txs_count_in_block(block_id: int) -> int:
    return Transaction.objects.using("java_wallet").filter(block_id=block_id).count()


def get_pool_id_for_block(block: Block) -> int:
    elapsed = datetime.now() - block.timestamp

    # For the more recent blocks we do not use the cache, since we could have short lived forks
    if elapsed.total_seconds() < 240*4:
        return get_pool_id_for_block_db(block)
    return get_pool_id_for_block_cached(block)

def get_pool_id_for_block_db(block: Block) -> int:
    return (
        Transaction.objects.using("java_wallet")
        .filter(type=TxType.BURST_MINING, subtype=TxSubtypeBurstMining.REWARD_RECIPIENT_ASSIGNMENT,
            height__lte=block.height, sender_id=block.generator_id)
        .values_list("recipient_id", flat=True)
        .order_by("-height")
        .first()
    )

@cache_memoize(3600 * 24)
def get_total_circulating():
    return (
        Account.objects.using("java_wallet")
        .filter(latest=True)
        .exclude(id=0)
        .aggregate(Sum("balance"))["balance__sum"]
    )

@cache_memoize(3600 * 24)
def get_total_accounts_count():
    return (
        Account.objects.using("java_wallet")
        .filter(latest=True)
        .exclude(id=0)
        .count()
    )

@cache_memoize(None)
def get_pool_id_for_block_cached(block: Block) -> int:
    return get_pool_id_for_block_db(block)

@cache_memoize(3600)
def get_pool_id_for_account(address_id: int) -> int:
    return (
        RewardRecipAssign.objects.using("java_wallet")
        .filter(account_id=address_id)
        .values_list("recip_id", flat=True)
        .order_by("-height")
        .first()
    )


@cache_memoize(60)
def get_unconfirmed_transactions():
    txs_pending = BrsApi(settings.SIGNUM_NODE).get_unconfirmed_transactions()

    for t in txs_pending:
        t["timestamp"] = datetime.fromtimestamp(
            t["timestamp"] + BLOCK_CHAIN_START_AT
        )
        t["amountNQT"] = int(t["amountNQT"])
        t["feeNQT"] = int(t["feeNQT"])
        t["sender_name"] = get_account_name(int(t["sender"]))

        if "recipient" in t:
            t["recipient_exists"] = (
                Account.objects.using("java_wallet")
                .filter(id=t["recipient"])
                .exists()
            )
            if t["recipient_exists"]:
                t["recipient_name"] = get_account_name(int(t["recipient"]))

        t["attachment_bytes"] = None
        if "attachmentBytes" in t:
            t["attachment_bytes"] =  bytes.fromhex(t["attachmentBytes"])
        if "attachment" in t and "recipients" in t["attachment"]:
            t["multiout"] = len(t["attachment"]["recipients"])

        t["tx_name"] = get_desc_tx_type(t["type"], t["subtype"])

    txs_pending.sort(key=lambda _x: _x["feeNQT"], reverse=True)

    return txs_pending
