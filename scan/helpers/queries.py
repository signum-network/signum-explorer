import time
import os

from ctypes import c_ulonglong, c_longlong
from datetime import datetime
from MySQLdb import Timestamp
from django.conf import settings

from django.db.models import Sum

from cache_memoize import cache_memoize
from burst.api.brs.v1.api import BrsApi
from burst.constants import BLOCK_CHAIN_START_AT, TxSubtypeBurstMining, TxSubtypeColoredCoins, TxType
from java_wallet.fields import get_desc_tx_type

from java_wallet.models import Account, AccountBalance, Asset, At, AtState, Block, RewardRecipAssign, Trade, Transaction,IndirecIncoming


@cache_memoize(3600)
def get_account_name(account_id: int) -> str:
    if account_id == 0:
        return "Burn Address"
    account_name = (
        Account.objects.using("java_wallet")
        .filter(id=account_id, latest=True)
        .values_list("name", flat=True)
        .first()
    )
    if not account_name:
        account_name = (
            At.objects.using("java_wallet")
            .filter(id=account_id, latest=True)
            .values_list("name", flat=True)
            .first()
        )
    return account_name

@cache_memoize(240)
def get_account_balance(account_id: int) -> str:
    account_balance = (
        AccountBalance.objects.using("java_wallet")
        .filter(id=account_id, latest=True)
        .values_list("balance", flat=True)
        .first()
    )
    if account_balance:
        return account_balance
    else :
        return 0

@cache_memoize(200)
def get_account_unconfirmed_balance(account_id: int) -> str:
    account_balance = (
        AccountBalance.objects.using("java_wallet")
        .filter(id=account_id, latest=True)
        .values_list("unconfirmed_balance", flat=True)
        .first()
    )
    if account_balance:
        return account_balance
    else:
        return 0

@cache_memoize(3600)
def get_details_by_tx(transaction_id:int) -> ( int, int,int):
    # Value = Sender, Reciepent,Timestamp
    transactions_data = (
        Transaction.objects.using("java_wallet")
        .filter(id =transaction_id )
        .values_list("recipient_id","sender_id","timestamp")
        .first()
    )
    return transactions_data

@cache_memoize(3600)
def get_single_tx_class(transaction_id:int):
    # Value = Sender, Reciepent,Timestamp
    transactions_data = (
        Transaction.objects.using("java_wallet")
        .filter(id =transaction_id )
        .first()
    )
    return transactions_data

# @cache_memoize(None)
def get_ap_code(ap_code_hash_id: int) -> bytearray:
    ap_code = (
        At.objects.using("java_wallet")
        .filter(ap_code_hash_id=ap_code_hash_id, ap_code__isnull=False)
        .values_list("ap_code", flat=True)
        .first()
    )
    return ap_code

def get_at_state(id: int) -> (bytearray, int):
    return (        
        AtState.objects.using("java_wallet")
        .filter(at_id=id, latest=True)
        .values_list("state", "min_activate_amount")
        .first()
        )

@cache_memoize(None)
def check_is_contract(account_id: int) -> bool:
    at_id = (
            At.objects.using("java_wallet")
            .filter(id=account_id, latest=True)
            .values_list("id", flat=True)
            .first()
        )
    return at_id != None

@cache_memoize(None)
def query_asset_treasury_acc(asset, account_id) -> (str, str):
    full_hash = (Transaction.objects.using("java_wallet")
        .values_list('full_hash', flat=True)
        .filter(id=asset.asset_id).first()
    )
    add_treasury = (Transaction.objects.using("java_wallet")
        .values_list('referenced_transaction_fullhash')
        .filter(sender_id=asset.owner_id, type=TxType.COLORED_COINS,
            subtype=TxSubtypeColoredCoins.ADD_TREASURY_ACCOUNT,
            recipient_id=account_id ).all()
    )
    
    return full_hash, add_treasury

@cache_memoize(None)
def get_asset_details(asset_id: int) -> (str, int, int, bool):
    asset_details = (
        Asset.objects.using("java_wallet")
        .filter(id=asset_id)
        .values_list("name", "decimals", "quantity", "mintable")
        .first()
        )
    return asset_details

@cache_memoize(None)
def get_asset_details_owner(asset_id: int) -> (str, int, int, bool, int):
    asset_details = (
        Asset.objects.using("java_wallet")
        .filter(id=asset_id)
        .values_list("name", "decimals", "quantity", "mintable", "account_id")
        .first()
        )
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

@cache_memoize(240)
def get_total_circulating():
    return (
        AccountBalance.objects.using("java_wallet")
        .filter(latest=True)
        .exclude(id=0)
        .aggregate(Sum("balance"))["balance__sum"] 
    )  

@cache_memoize(3600)
def get_total_accounts_count():
    return (
        Account.objects.using("java_wallet")
        .filter(latest=True)
        .exclude(id=0)
        .count()
    )

@cache_memoize(300)
def get_asset_price(asset_id : int) -> float:
    latest_trade = assets_trades = (
        Trade.objects.using("java_wallet")
        .using("java_wallet")
        .filter(asset_id=asset_id)
        .order_by("-height").first()
    )
    if latest_trade:
        return latest_trade.price
    return 0

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


@cache_memoize(10)
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

@cache_memoize(10)
def get_unconfirmed_transactions_index():
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

        t["tx_name"] = get_desc_tx_type(t["type"], t["subtype"])
        
    txs_pending.sort(key=lambda _x: _x["feeNQT"], reverse=True)

    return txs_pending
