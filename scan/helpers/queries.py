import datetime, time
import os

from cache_memoize import cache_memoize
from burst.constants import TxSubtypeBurstMining, TxType

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
    elapsed = datetime.datetime.now() - block.timestamp

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
