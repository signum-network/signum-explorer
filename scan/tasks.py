import logging
import os

from time import sleep
from django.conf import settings
from config.settings import TASKS_SCAN_DELAY
from scan.caching_data.exchange import CachingExchangeData

#from scan.caching_data.total_accounts_count import CachingTotalAccountsCount
#from scan.caching_data.total_txs_count import CachingTotalTxsCount

logger = logging.getLogger(__name__)

def task_cmd():
    if TASKS_SCAN_DELAY > 0:
        logger.info(f"Tasks Sleeping for {TASKS_SCAN_DELAY} seconds...")
    sleep(TASKS_SCAN_DELAY)
    logger.info("TASK - Update Cache Exchange data")
    CachingExchangeData().update_live_data()



#    def update_cache_total_txs_count():
#        logger.info("TASK - Update Total TX's count data")
#        CachingTotalTxsCount().update_live_data()


#    def update_cache_total_accounts_count():
#        logger.info("TASK - Update Total Accounts data")
#        CachingTotalAccountsCount().update_live_data()
