import logging
import os

from time import sleep
from django.conf import settings
from config.settings import TASKS_SCAN_DELAY
from scan.caching_data.exchange import CachingExchangeData
from scan.caching_data.total_txs_count import CachingTotalTxsCount
from scan.caching_data.total_circulating import CachingTotalCirculating
#from scan.caching_data.total_accounts_count import CachingTotalAccountsCount

logger = logging.getLogger(__name__)

######################################
# These tasks run on a regular       #
# interval, currently 60 sec         #
# via a remote script or supervisord #
# By loading cache via a task it     #
# saves the user from a slow initial #
# page load.                         #
######################################

def task_cmd():
    if TASKS_SCAN_DELAY > 0:  # Delay in env used when supervisord is used.
        logger.info(f"Tasks Sleeping for {TASKS_SCAN_DELAY} seconds...")
        
######### Update Exchange #########
    sleep(TASKS_SCAN_DELAY)
    logger.info("TASK - Update Cache Exchange data")
    CachingExchangeData().update_live_data()
    
######### Update Total TX #########
    logger.info("TASK - Update Total TX's count data")
    CachingTotalTxsCount().update_live_data()

######### Update Total Circulating #########
    logger.info("TASK - Update Total Circulating data")
    CachingTotalCirculating().update_live_data()

#    def update_cache_total_accounts_count():
#        logger.info("TASK - Update Total Accounts data")
#        CachingTotalAccountsCount().update_live_data()
