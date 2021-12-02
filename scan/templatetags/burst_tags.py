from datetime import datetime, timedelta
from math import ceil
import sys

from django import template
from django.conf import settings

from burst.constants import MAX_BASE_TARGET, TxSubtypeBurstMining, TxSubtypeColoredCoins, TxSubtypePayment, TxType
from burst.libs.functions import calc_block_reward
from burst.libs.multiout import MultiOutPack
from burst.libs.reed_solomon import ReedSolomon
from burst.libs.transactions import get_message
from burst.api.brs.v1.api import BrsApi

from java_wallet.fields import get_desc_tx_type
from java_wallet.models import Block, IndirectRecipient, Transaction
from scan.caching_data.exchange import CachingExchangeData

import struct
import os

from scan.helpers.queries import get_asset_details

register = template.Library()


@register.filter
def block_reward(block: Block) -> int:
    return calc_block_reward(block.height)


@register.filter
def block_reward_with_fee(block: Block) -> float:
    return calc_block_reward(block.height) + block.total_fee / 10 ** 8

@register.filter
def asset_circulating(asset_id: int) -> int:
    version = os.environ.get('BRS_P2P_VERSION')
    asset_details = BrsApi(settings.SIGNUM_NODE).get_asset(asset_id)

    if version.startswith('3.3'):
        return int(asset_details["quantityCirculatingQNT"])
    return int(asset_details["quantityQNT"])

@register.filter
def burst_amount(value: int) -> float:
    return round(value / 100000000.0, 8)

@register.filter
def append_symbol(value: float) -> str:
    return value + " " + os.environ.get("COIN_SYMBOL")

@register.simple_tag()
def coin_symbol() -> str:
    return os.environ.get("COIN_SYMBOL")

@register.filter
def env(key):
    return os.environ.get(key, None)

@register.filter
def in_usd(value: float) -> float:
    data = CachingExchangeData().cached_data
    return value * data.price_usd


@register.filter
def rounding(value: float, accuracy: int) -> float:
    return round(value, accuracy)


@register.filter
def bin2hex(value: bytes) -> str:
    if not value:
        return ""
    return value.hex().upper()


@register.filter
def tx_message(tx: Transaction) -> str:
    if not tx.has_message:
        return ""
    return get_message(tx.attachment_bytes)

@register.filter
def tx_type(tx: Transaction) -> str:
    return get_desc_tx_type(tx.type, tx.subtype)

@register.filter
def tx_amount(tx: Transaction) -> int:
    if tx.type == TxType.BURST_MINING and (tx.subtype == TxSubtypeBurstMining.COMMITMENT_ADD or tx.subtype == TxSubtypeBurstMining.COMMITMENT_REMOVE):
        return int.from_bytes(tx.attachment_bytes[1:], byteorder=sys.byteorder)

    elif tx.type == TxType.COLORED_COINS:
        if tx.subtype == TxSubtypeColoredCoins.ASSET_TRANSFER:
            asset_id = int.from_bytes(tx.attachment_bytes[1:9], byteorder=sys.byteorder)
            name, decimals, total_quantity, mintable = get_asset_details(asset_id)
            quantity = int.from_bytes(tx.attachment_bytes[9:17], byteorder=sys.byteorder)
            return mul_decimals(quantity, 8-decimals)

        elif tx.subtype in [TxSubtypeColoredCoins.ASK_ORDER_PLACEMENT, TxSubtypeColoredCoins.BID_ORDER_PLACEMENT]:
            quantity = int.from_bytes(tx.attachment_bytes[9:17], byteorder=sys.byteorder)
            price = int.from_bytes(tx.attachment_bytes[18:27], byteorder=sys.byteorder)
            return quantity*price

    return tx.amount

@register.filter
def tx_symbol(tx: Transaction) -> str:
    if tx.type == TxType.COLORED_COINS:
        if tx.subtype == TxSubtypeColoredCoins.ASSET_TRANSFER:
            asset_id = int.from_bytes(tx.attachment_bytes[1:9], byteorder=sys.byteorder)
            name, decimals, total_quantity, mintable = get_asset_details(asset_id)
            return name.upper()

    return coin_symbol()

def group_list(lst: list or tuple, n: int):
    for i in range(0, len(lst), n):
        val = lst[i : i + n]
        if len(val) == n:
            yield tuple(val)

@register.filter
def tx_load_recipients(tx: Transaction) -> Transaction:
    if not tx.recipients:
        if tx.type == TxType.PAYMENT and tx.subtype == TxSubtypePayment.MULTI_OUT:
            data = MultiOutPack().unpack_multi_out(tx.attachment_bytes)
            recipients = []
            amounts = []
            for r, a in group_list(data, 2):
                recipient = IndirectRecipient()
                recipient.amount = a
                recipient.id = r
                recipients.append(recipient)
            tx.recipients = recipients
        elif tx.type == TxType.PAYMENT and tx.subtype == TxSubtypePayment.MULTI_OUT_SAME:
            data = MultiOutPack().unpack_multi_out_same(tx.attachment_bytes)
            recipients = []
            for r in data:
                recipient = IndirectRecipient()
                recipient.amount = tx.amount / len(data)
                recipient.id = r
                recipients.append(recipient)

            tx.recipients = recipients
    return tx

@register.filter
def num2rs(value: str or int) -> str:
    return os.environ.get("ADDRESS_PREFIX") + ReedSolomon().encode(str(value))


@register.simple_tag()
def block_generation_time(block: Block) -> timedelta:
    if block.previous_block:
        return block.timestamp - block.previous_block.timestamp
    else:
        # first block
        return timedelta(0)


@register.filter
def sub(a: int or float, b: int or float) -> int or float:
    return a - b


@register.filter
def div(a: int or float, b: int or float) -> float:
    return a / b


@register.filter
def mul(a: int or float, b: int or float) -> int or float:
    return a * b


@register.filter
def div_decimals(a: int or float, b: int) -> float:
    return a / 10 ** b


@register.filter
def mul_decimals(a: int or float, b: int) -> float:
    return a * 10 ** b


@register.filter
def percent(value: int or float, total: int or float) -> int or float:
    return value / total * 100


@register.filter
def net_capacity_tib(base_target: int) -> float:
    if base_target < 100000000000:
        return MAX_BASE_TARGET / (base_target)
    s = struct.pack('>l', base_target & 0xFFFFFFFF)
    base_target_capacity = struct.unpack('>f', s)[0]
    return MAX_BASE_TARGET / (1.83 * base_target_capacity)

@register.filter
def format_capacity(capacity: float) -> str:
    unit = "TiB"
    if capacity > 10000:
        capacity = capacity/1024
        unit = "PiB"
    return "{:.1f}".format(capacity) + " " + unit

@register.filter
def net_commitment(base_target: int) -> float:
    if base_target < 100000000000:
        return 1000
    s = struct.pack('>l', base_target >> 32)
    avg_commitment = struct.unpack('>f', s)[0]
    return avg_commitment/100000000.0

@register.simple_tag(takes_context=True)
def rank_row(context: dict, number: int) -> int:
    start = 0
    if context["page_obj"].number > 0:
        start = context["paginator"].per_page * (context["page_obj"].number - 1)

    return number + start


@register.filter
def tx_deadline(value):
    return value["timestamp"] + timedelta(minutes=value["deadline"]) - datetime.now()


@register.filter()
def smooth_timedelta(timedelta_obj):
    secs = timedelta_obj.total_seconds()
    time_str = ""
    if secs > 86400:  # 60sec * 60min * 24hrs
        days = secs // 86400
        time_str += f"{int(days)} d"
        secs = secs - days * 86400

    if secs > 3600:
        hours = secs // 3600
        time_str += f" {int(hours)} h"
        secs = secs - hours * 3600

    if secs > 60:
        minutes = ceil(secs / 60)
        time_str += f" {int(minutes)} min"

    if not time_str:
        time_str = f"{int(secs)} seconds"

    return time_str
