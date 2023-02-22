import logging
import os

from time import sleep
from django.conf import settings
from config.settings import TASKS_SCAN_DELAY
from scan.caching_data.exchange import CachingExchangeData
from celery import shared_task
from scan.caching_data.total_txs_count import CachingTotalTxsCount
from scan.caching_data.total_circulating import CachingTotalCirculating
#from scan.caching_data.total_accounts_count import CachingTotalAccountsCount

logger = logging.getLogger(__name__)

from java_wallet.models import Transaction


######################################
# These tasks run on a regular       #
# interval, currently 60 sec         #
# via a remote script or supervisord #
# By loading cache via a task it     #
# saves the user from a slow initial #
# page load.                         #
######################################

@shared_task()
def runner_TxTotal():
    ######### Update Total TX #########
    CachingTotalTxsCount().update_live_data()
    logger.info("TASK - Updated TX's count data")

@shared_task()
def runner_Exchange():        
    ######### Update Exchange #########
    CachingExchangeData().update_live_data()
    logger.info("TASK - Updated Exchange data")

@shared_task
def runner_Circulating():
    ######### Update Total Circulating #########
    CachingTotalCirculating().update_live_data()
    logger.info("TASK - Updated Circulating data")

def task_cmd():
    while True:
        if TASKS_SCAN_DELAY > 0:  # Delay in env used when supervisord is used.
            logger.info(f"Tasks Sleeping for {TASKS_SCAN_DELAY} seconds...")
        runner_Exchange.delay()
        runner_TxTotal.delay()
        runner_Circulating.delay()
        sleep(TASKS_SCAN_DELAY)
#    def update_cache_total_accounts_count():
#        logger.info("TASK - Update Total Accounts data")
#        CachingTotalAccountsCount().update_live_data()