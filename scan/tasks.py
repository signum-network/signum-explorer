import json, logging, os, requests
from time import sleep
from django.conf import settings
from config.settings import (
    TASKS_SCAN_DELAY, 
    SNR_MASTER_EXPLORER,
    BRS_BOOTSTRAP_PEERS,
    AUTO_BOOTSTRAP_PEERS,
)
from scan.models import PeerMonitor
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
        
############# Update Exchange ############## (change to 60 sec update)
    sleep(TASKS_SCAN_DELAY)
    logger.info("TASK - Update Cache Exchange data")
    CachingExchangeData().update_live_data()
    
############## Update Total TX ############# (match block time, heavy db request)
    logger.info("TASK - Update Total TX's count data")
    CachingTotalTxsCount().update_live_data()

######### Update Total Circulating ######### (match block time, heavy db request)
    logger.info("TASK - Update Total Circulating data")
    CachingTotalCirculating().update_live_data()
    
######### Update Peers SNR Status ########## (change to 6 hours update)
    if SNR_MASTER_EXPLORER :
        logger.info("TASK - Update Peer SNR data")
        snr_master = list(requests.get(url=SNR_MASTER_EXPLORER + "/json/SNRinfo").json())
        for node in snr_master:
            PeerMonitor.objects.filter(announced_address=node[0]).update(reward_state=node[2], reward_time=node[3])
        if snr_master :
            logger.info("SNR Master Data Received")

    """
    ######### Update Bootstrap Peers ###########
        Best to run this task instead of having the page load it each time it's opened. 
        Also exports to env for peer scan use. 
    """
    if AUTO_BOOTSTRAP_PEERS:
        bootstrap_peers = BRS_BOOTSTRAP_PEERS
        auto_bootstrap_peers = (
            PeerMonitor.objects
            .filter(announced_address__contains='.signum.network')
            .exclude(state__gt=1)
            .values_list(flat=True)
        )
        bootstrap_peers = list(set(list(auto_bootstrap_peers) + list(bootstrap_peers)))
        if bootstrap_peers:
            logger.info(f"Bootstrap Peers Updated: {bootstrap_peers}")
        os.environ["BRS_BOOTSTRAP_PEERS"] = json.dumps(bootstrap_peers)

#    def update_cache_total_accounts_count():
#        logger.info("TASK - Update Total Accounts data")
#        CachingTotalAccountsCount().update_live_data()
