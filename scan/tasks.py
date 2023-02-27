import logging, os, requests, json
from time import sleep
from django.conf import settings
from config.settings import SNR_MASTER_EXPLORER
from scan.caching_data.exchange import CachingExchangeData
from scan.caching_data.total_txs_count import CachingTotalTxsCount
from scan.caching_data.total_circulating import CachingTotalCirculating
from scan.models import PeerMonitor
from celery import Celery
from config.celery import app

logger = logging.getLogger(__name__)

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
    logger.info("TASK - Updated TX's count data")

@app.task
def runner_Exchange():        
    ######### Update Exchange #########
    CachingExchangeData().update_live_data()
    logger.info("TASK - Updated Exchange data")

@app.task
def runner_Circulating():
    ######### Update Total Circulating #########
    CachingTotalCirculating().update_live_data()
    logger.info("TASK - Updated Circulating data")

@app.task
def update_MasterSNR():
    try: snr_master = list(requests.get(url=SNR_MASTER_EXPLORER + "/json/SNRinfo").json())
    except: snr_master = []
    for node in snr_master:
        PeerMonitor.objects.filter(announced_address=node[0]).update(reward_state=node[2], reward_time=node[3])
    logger.info("TASK - Updated MasterExplorer data")

def task_cmd():
    logger.info(f"Force running task updates...")
    runner_Exchange.delay()
    runner_TxTotal.delay()
    runner_Circulating.delay()
    update_MasterSNR.delay()

    #    def update_cache_total_accounts_count():
    #        logger.info("TASK - Update Total Accounts data")
    #        CachingTotalAccountsCount().update_live_data()