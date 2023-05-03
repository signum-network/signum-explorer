import os, requests, json
from config.settings import SNR_MASTER_EXPLORER

from scan.caching_data.exchange import CachingExchangeData
from scan.caching_data.total_txs_count import CachingTotalTxsCount
from scan.caching_data.total_circulating import CachingTotalCirculating
from scan.models import PeerMonitor
from scan.helpers.decorators import skip_if_running

from celery import shared_task
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

@shared_task(bind=True)
@skip_if_running
def runner_TxTotal(self):
    ######### Update Total TX #########
    CachingTotalTxsCount().update_live_data()
    logger.debug("TASK - Updated TX's count data")

@shared_task(bind=True)
@skip_if_running
def runner_Exchange(self):        
    ######### Update Exchange #########
    CachingExchangeData().update_live_data()
    logger.debug("TASK - Updated Exchange data")

@shared_task(bind=True)
@skip_if_running
def runner_Circulating(self):
    ######### Update Total Circulating #########
    CachingTotalCirculating().update_live_data()
    logger.debug("TASK - Updated Circulating data")

@shared_task(bind=True)
@skip_if_running
def update_MasterSNR(self):
    try: 
        snr_master = list(requests.get(url=SNR_MASTER_EXPLORER + "/json/SNRinfo").json())
        logger.debug(f"TASK - SNR Response Received")
    except: 
        snr_master = []
        logger.warning("TASK - No SNR Received!")
    for node in snr_master:
        PeerMonitor.objects.filter(announced_address=node[0]).update(reward_state=node[2], reward_time=node[3])
    logger.debug("TASK - Updated MasterExplorer data")

def task_cmd():
    logger.info(f"Force running task updates...")
    runner_Exchange.delay()
    runner_TxTotal.delay()
    runner_Circulating.delay()
    update_MasterSNR.delay()

    #    def update_cache_total_accounts_count():
    #        logger.info("TASK - Update Total Accounts data")
    #        CachingTotalAccountsCount().update_live_data()