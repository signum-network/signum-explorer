import logging, os, requests, json, random, socket
from time import sleep
from math import log
from requests.exceptions import RequestException
from datetime import timedelta
from distutils.version import LooseVersion
from urllib.parse import urlparse
from functools import wraps

from django.conf import settings
from config.settings import SNR_MASTER_EXPLORER
from django import forms
from django.db import transaction
from django.db.models import DurationField, ExpressionWrapper, F
from django.db.models.functions import Now
from django.utils import timezone

from scan.caching_data.exchange import CachingExchangeData
from scan.caching_data.total_txs_count import CachingTotalTxsCount
from scan.caching_data.total_circulating import CachingTotalCirculating
from scan.models import PeerMonitor
from burst.api.brs.p2p import P2PApi
from burst.api.exceptions import BurstException
from java_wallet.models import Block
from scan.helpers.decorators import skip_if_running

from celery import Celery, shared_task
from config.celery import app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

######################################
# These tasks run on a regular       #
# interval, currently 60 sec         #
# via a remote script or supervisord #
# By loading cache via a task it     #
# saves the user from a slow initial #
# page load.                         #
######################################

@app.task
def runner_TxTotal():
    ######### Update Total TX #########
    CachingTotalTxsCount().update_live_data()
    logger.debug("TASK - Updated TX's count data")

@app.task
def runner_Exchange():        
    ######### Update Exchange #########
    CachingExchangeData().update_live_data()
    logger.debug("TASK - Updated Exchange data")

@app.task
def runner_Circulating():
    ######### Update Total Circulating #########
    CachingTotalCirculating().update_live_data()
    logger.debug("TASK - Updated Circulating data")

@app.task
def update_MasterSNR():
    try: 
        snr_master = list(requests.get(url=SNR_MASTER_EXPLORER + "/json/SNRinfo").json())
        logger.debug(f"TASK - SNR Response Received")
    except: 
        snr_master = []
        logger.warning("TASK - No SNR Received!")
    for node in snr_master:
        PeerMonitor.objects.filter(announced_address=node[0]).update(reward_state=node[2], reward_time=node[3])
    logger.debug("TASK - Updated MasterExplorer data")

def task_testing():
    latest_blocks = (
        Block.objects.using("java_wallet")
        .order_by("-height")
        .values("height", "cumulative_difficulty", "id")[:3]
    )
    result = latest_blocks[1]

    result["cumulative_difficulty"] = str(
        int(result["cumulative_difficulty"].hex(), 16)
    )
    print(result["cumulative_difficulty"])


def task_cmd():
    logger.info(f"Force running task updates...")
    task_testing()
    #runner_Exchange.delay()
    #runner_TxTotal.delay()
    #runner_Circulating.delay()
    #update_MasterSNR.delay()

    #    def update_cache_total_accounts_count():
    #        logger.info("TASK - Update Total Accounts data")
    #        CachingTotalAccountsCount().update_live_data()