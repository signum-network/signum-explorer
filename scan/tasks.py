import logging, os, requests, json, random, socket
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

class PeerMonitorForm(forms.ModelForm):
    class Meta:
        model = PeerMonitor
        fields = ['announced_address', 'real_ip', 'platform', 'application', 'version', 'height', 'cumulative_difficulty', 'country_code', 'state', 'downtime', 'lifetime', 'availability', 'last_online_at']


def is_good_version(version: str) -> bool:
    if not version:
        return False
    if version[0] == "v":
        version = version[1:]

    try:
        return LooseVersion(version) >= LooseVersion(settings.MIN_PEER_VERSION)
    except TypeError:
        return False

@shared_task(bind=True)
@skip_if_running
@transaction.atomic
def peer_cmd(self):
    latest_blocks = (
        Block.objects.using("java_wallet")
        .order_by("-height")
        .values("height", "cumulative_difficulty", "id")[:3]
    )
    result = latest_blocks[1]

    result["cumulative_difficulty"] = str(
        int(result["cumulative_difficulty"].hex(), 16)
    )
    result["previous_block_id"] = latest_blocks[2]["id"]
    local_difficulty = result

    logger.info(f"Checking for height:\n{local_difficulty['height']}, id: {local_difficulty['id']}, prev id: {local_difficulty['previous_block_id']}")

    addresses_offline = (
        list(
            PeerMonitor.objects.values_list("announced_address", flat=True)
            .filter(state=PeerMonitor.State.UNREACHABLE)
            .distinct()
        )
        or []
    )

    # get other addresses exclude UNREACHABLE
    addresses_other = (
        list(
            PeerMonitor.objects.values_list("announced_address", flat=True)
            .exclude(state=PeerMonitor.State.UNREACHABLE)
            .distinct()
        )
        or []
    )

    # add well-known peers
    addresses_other.extend(settings.BRS_BOOTSTRAP_PEERS)

    # mix it
    random.shuffle(addresses_offline)
    random.shuffle(addresses_other)

    # first UNREACHABLE
    addresses = addresses_offline + addresses_other

    logger.info(f"The list of peers:\n{addresses}") #enable to troubleshoot peers list
    # explore every peer and collect updates
    updates = {}
    for address in addresses:
        logger.debug("Node: %s", address)
        try:
            peers = P2PApi(address).get_peers()
        except BurstException:
            logger.debug("Can't connect to node: %s", address)
            pass
        else:
            for peer in peers:
                logger.debug("Peer: %s", address)

                if address in updates:
                    pass

                try:
                    p2p_api = P2PApi(address)
                    peer_info = p2p_api.get_info()
                    if not peer_info:
                        updates[address] = None
                        pass
                    if not is_good_version(peer_info["version"]):
                        logger.debug("Old version: %s", peer_info["version"])
                        updates[address] = None
                        pass
                    if not "announcedAddress" in peer_info:
                        peer_info["announcedAddress"] = address

                    default_port = ":" + str(settings.DEFAULT_P2P_PORT)
                    peer_info["announcedAddress"] = peer_info["announcedAddress"].replace(default_port,"")
                    peer_info.update(p2p_api.get_cumulative_difficulty())
                    peer_info["next_block_ids"] = []
                    try:
                        peer_info["next_block_ids"] = p2p_api.get_next_block_ids(local_difficulty["previous_block_id"])
                    except:
                        logger.debug("Could not get next block ids for " + p2p_api.node_url)
                except BurstException as ex:
                    logger.debug("Can't connect to peer: %s", p2p_api.node_url)
                    updates[address] = None
                    pass

                ip = ""

                if not peer.startswith("http"):
                    peer = f"http://{peer}"
                hostname = urlparse(peer).hostname

                if not hostname:
                    ip = None

                # ipv6
                if ":" in hostname:
                    ip = hostname

                try:
                    ip = socket.gethostbyname(hostname)
                except socket.gaierror as e:
                    logger.debug("Can't resolve host: %s - %r", peer, e)
                    ip = None

                try:
                    response = requests.get(f"https://ipwho.is/{ip}")
                    response.raise_for_status()
                    json_response = response.json()
                    georesponse = json_response["continent"] or "??"
                    logger.debug("Geo lookup, found peer from: %s", georesponse)
                    get_country_by_ip = json_response["country_code"] or "??"
                except (RequestException, ValueError, KeyError):
                    logger.debug("Geo lookup ERROR!")
                    get_country_by_ip = "??"

                updates[address] = {
                    "announced_address": peer_info["announcedAddress"],
                    "real_ip": ip,
                    "country_code": get_country_by_ip,
                    "application": peer_info["application"],
                    "platform": peer_info["platform"],
                    "version": peer_info["version"],
                    "height": peer_info["blockchainHeight"],
                    "cumulative_difficulty": peer_info["cumulativeDifficulty"],
                    "last_online_at": timezone.now(),
                    "next_block_ids": peer_info["next_block_ids"],
                }

    updates_with_data = tuple(filter(lambda x: x is not None, updates.values()))
    # if more than __% peers were gone offline in __min, probably network problem
    if len(updates_with_data) < (PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE).count() * 0.8):
        logger.warning(
            "Peers update was rejected: %d - %d", len(updates_with_data), len(addresses)
        )
        return

    # set all peers unreachable, if will no update - peer will be unreachable
    PeerMonitor.objects.update(state=PeerMonitor.State.UNREACHABLE)

    # calculate state and apply updates
    for update in updates_with_data:
        logger.debug("Update: %r", update)

        peer_obj = PeerMonitor.objects.filter(
            announced_address=update["announced_address"]
        ).first()
        if not peer_obj:
            logger.info("Found new peer: %s", update["announced_address"])

        check_id = str(local_difficulty["id"])

        if update["height"] > local_difficulty["height"]:
            if check_id in update["next_block_ids"]:
                state = PeerMonitor.State.ONLINE
            else:
                state = PeerMonitor.State.FORKED
        else:
            if peer_obj and peer_obj.height == update["height"]:
                state = PeerMonitor.State.STUCK
            else:
                _cumulative_difficulty = str(int(
                        Block.objects.using("java_wallet")
                        .filter(height=update["height"])
                        .values_list("cumulative_difficulty", flat=True)
                        .first()
                    ).hex(), 16)
                if update["cumulative_difficulty"] == _cumulative_difficulty:
                    state = PeerMonitor.State.SYNC
                else:
                    state = PeerMonitor.State.FORKED

        update["state"] =  state

        form = PeerMonitorForm(update, instance=peer_obj)

        if form.is_valid():
            form.save()
        else:
            logger.warning("Not valid data: %r - %r", form.errors, update)

    PeerMonitor.objects.update(lifetime=F("lifetime") + 1)

    PeerMonitor.objects.filter(
        state__in=[PeerMonitor.State.UNREACHABLE, PeerMonitor.State.STUCK, PeerMonitor.State.FORKED]
    ).update(downtime=F("downtime") + 1)

    PeerMonitor.objects.annotate(
        duration=ExpressionWrapper(
            Now() - F("last_online_at"), output_field=DurationField()
        )
    ).filter(duration__gte=timedelta(days=5)).delete()

    PeerMonitor.objects.update(
        availability=100 - (F("downtime") / F("lifetime") * 100),
        modified_at=timezone.now(),
    )

    logger.debug("Peer Update Done")

def task_cmd():
    logger.info(f"Force running task updates...")
    runner_Exchange.delay()
    runner_TxTotal.delay()
    runner_Circulating.delay()
    update_MasterSNR.delay()

    #    def update_cache_total_accounts_count():
    #        logger.info("TASK - Update Total Accounts data")
    #        CachingTotalAccountsCount().update_live_data()