import random
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from distutils.version import LooseVersion
from functools import lru_cache
from urllib.parse import urlparse
from time import sleep

import requests
import ipapi
import geoip2.database

from cache_memoize import cache_memoize
from django import forms
from django.conf import settings
from django.db import transaction
from django.db.models import DurationField, ExpressionWrapper, F
from django.db.models.functions import Now
from django.utils import timezone
from requests.exceptions import RequestException

from burst.api.brs.p2p import P2PApi
from burst.api.exceptions import BurstException
from config.settings import PEERS_SCAN_DELAY
from java_wallet.models import Block
from scan.helpers.decorators import lock_decorator
from scan.models import PeerMonitor
from scan.helpers.decorators import skip_if_running

from celery import Celery, shared_task
from config.celery import app
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

# https://github.com/P3TERX/GeoLite.mmdb
_reader = geoip2.database.Reader('static/ip_database/GeoLite2-Country.mmdb')

def get_ip_by_domain(peer: str) -> str or None:
    # truncating port if exists
    if not peer.startswith("http"):
        peer = f"http://{peer}"
    hostname = urlparse(peer).hostname

    if not hostname:
        return None

    # ipv6
    if ":" in hostname:
        return hostname

    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        logger.debug("Can't resolve host: %s - %r", peer, e)
        return None


@cache_memoize(60 * 60 * 24 * 7)
def get_country_by_ip(ipa: str) -> str:
    """geoip2"""
    try:
        cc = _reader.country(ipa).country.iso_code
        logger.debug(f"Geo lookup 1 - {ipa} country code: {cc}")
        if not cc or cc == "Undefined":
            raise Exception(f"{ipa} not in local database")
    except Exception as e:
        """Limits: 1k/day 30k/mo"""
        logger.debug(f"Geo lookup 1 failed - {e}\n")
        try:
            cc = ipapi.location(ip=ipa, output='country_code')
            logger.debug(f"Geo lookup 2 - {ipa} country code: {cc}")
        except(RequestException, ValueError, KeyError):
            logger.debug("Geo lookup 2 ERROR!")
    return cc or "??"

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


def get_local_difficulty() -> dict:
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

    return result


@lru_cache(maxsize=None)
def get_block_cumulative_difficulty(height: int) -> str:
    cumulative_difficulty = (
        Block.objects.using("java_wallet")
        .filter(height=height)
        .values_list("cumulative_difficulty", flat=True)
        .first()
    )
    return str(int(cumulative_difficulty.hex(), 16))


def explore_peer(local_difficulty: dict, address: str, updates: dict):
    logger.debug("Peer: %s", address)

    if address in updates:
        return

    try:
        p2p_api = P2PApi(address)
        peer_info = p2p_api.get_info()
        if not is_good_version(peer_info["version"]):
            logger.debug("Old version: %s", peer_info["version"])
            updates[address] = None
            return
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
        return

    ip = get_ip_by_domain(address)
    cc = get_country_by_ip(ip)
    if cc == "??" or cc == "Undefined":
        cc = get_country_by_ip(ip, _refresh=True)
        logger.debug(f"Force refresh of {ip} - New country: {cc}")

    updates[address] = {
        "announced_address": peer_info["announcedAddress"],
        "real_ip": ip,
        "country_code": str(cc),
        "application": peer_info["application"],
        "platform": peer_info["platform"],
        "version": peer_info["version"],
        "height": peer_info["blockchainHeight"],
        "cumulative_difficulty": peer_info["cumulativeDifficulty"],
        "last_online_at": timezone.now(),
        "next_block_ids": peer_info["next_block_ids"],
    }


def explore_node(local_difficulty: dict, address: str, updates: dict):
    logger.debug("Node: %s", address)

    try:
        peers = P2PApi(address).get_peers()
        explore_peer(local_difficulty, address, updates)
    except BurstException:
        logger.debug("Can't connect to node: %s", address)
        return

    if settings.DEBUG:
        for peer in peers:
            explore_peer(local_difficulty, peer, updates)
    else:
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(lambda p: explore_peer(local_difficulty, p, updates), peers)


def get_nodes_list() -> list:
    # first check UNREACHABLE because more chance they are still offline
    # and timeout connection in worker
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
    return addresses_offline + addresses_other


def check_state(local_difficulty: dict, update: dict, peer_obj: PeerMonitor or None) -> int:
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
            _cumulative_difficulty = get_block_cumulative_difficulty(update["height"])
            if update["cumulative_difficulty"] == _cumulative_difficulty:
                state = PeerMonitor.State.SYNC
            else:
                state = PeerMonitor.State.FORKED

    return state


def get_count_nodes_online() -> int:
    return PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE).count()

@shared_task(bind=True)
@skip_if_running
def peer_cleanup(*args):
    """
    Testing mostly, can be used manually to clean up junk peers by
    python manage.py peer_rescan
    """
    peers = PeerMonitor.objects.annotate(
            duration=ExpressionWrapper(
                Now() - F("last_online_at"), output_field=DurationField()
            )
        ).filter(Q(duration__gte=timedelta(days=3)) | Q(availability=0)).all()
    for peer in peers:
        logger.info(f"{peer} is stale and being deleted")
        peer.delete()

@shared_task(bind=True)
@skip_if_running
@transaction.atomic
def check_offline(*args):
    """
    Full scans can take some time, this scans offline peers only
    since the list can be much shorter and runs quickly
    """
    local_difficulty = get_local_difficulty()
    updates = {}
    peers = PeerMonitor.objects.filter(state=2).all()
    logger.debug(f"{len(peers)} are not 'considered' online. Starting update\n(This might take a few minutes...)")
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(lambda peer: explore_peer(local_difficulty, peer.announced_address, updates), peers)
    updates_with_data = tuple(filter(lambda x: x is not None, updates.values()))
    logger.debug(f"{len(updates_with_data)} peers can be updated")
    for update in updates_with_data:
        peer_obj = PeerMonitor.objects.filter(
            announced_address=update["announced_address"]
        ).first()
        update["state"] = check_state(local_difficulty, update, peer_obj)
        logger.debug(f"{update['announced_address']} is now {update['state']}")
        form = PeerMonitorForm(update, instance=peer_obj)
        if form.is_valid():
            form.save(commit=True)
            logger.debug(f"{update['announced_address']} should have been saved")
        elif peer_obj is not None:
            peer_obj.delete()
            logger.debug(f"Not valid data for:{update['announced_address']}\n{form.errors}\npeer being deleted")
        else:
            logger.debug(f"Not valid data for:{update['announced_address']}\n{form.errors}\npeer cannot be deleted")
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

@shared_task(bind=True)
@skip_if_running
@transaction.atomic
def peer_cmd(self):
    logger.debug("Start the scan")

    local_difficulty = get_local_difficulty()
    logger.info(f"Checking for height: {local_difficulty['height']}, id: {local_difficulty['id']}, prev id: {local_difficulty['previous_block_id']}")

    addresses = get_nodes_list()
    logger.debug(f"The list of peers:\n{addresses}") #enable to troubleshoot peers list
    #logger.debug(addresses)            #enable to troubleshoot peers list
    # explore every peer and collect updates
    updates = {}
    if settings.TEST_NET:
        for address in addresses:
            explore_node(local_difficulty, address, updates)
    else:
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(lambda address: explore_node(local_difficulty, address, updates), addresses)
    updates_with_data = tuple(filter(lambda x: x is not None, updates.values()))
    # if more than __% peers were gone offline in __min, probably network problem
    if len(updates_with_data) < get_count_nodes_online() * 0.8:
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
            logger.debug("Found new peer: %s", update["announced_address"])

        update["state"] = check_state(local_difficulty, update, peer_obj)

        form = PeerMonitorForm(update, instance=peer_obj)

        if form.is_valid():
            form.save()
        else:
            logger.debug("Not valid data: %r - %r", form.errors, update)

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

    logger.debug("Done")