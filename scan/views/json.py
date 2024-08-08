from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView
from config.settings import BRS_BOOTSTRAP_PEERS
from django.http import HttpResponse
from django.http import JsonResponse
from scan.models import PeerMonitor
from cache_memoize import cache_memoize

from java_wallet.models import (
    Account,
    AccountBalance,
    AccountAsset,
    Alias,
    Subscription,
    AssetTransfer,
    At,
    Block,
    IndirectIncoming,
    Trade,
    Transaction,
)

@cache_memoize(300)
@require_http_methods(["GET"])
def TopAccountsJson(request, results=10):
    bal = list(AccountBalance.objects.all().filter(latest=True,balance__gte=10000000000000).exclude(id=0).order_by('-balance').values('id', 'balance')[:results])
    return JsonResponse(bal, safe=False)

@cache_memoize(10)
@require_http_methods(["GET"])
def getStatejson(request, address):
    state = PeerMonitor.objects.only('state').get(announced_address=address).state
    return JsonResponse(state, safe=False)

@cache_memoize(10)
@require_http_methods(["GET"])
def getNodejson(request, address):
    noderaw = list(PeerMonitor.objects.all().filter(announced_address=address).values('announced_address', 'real_ip', 'platform', 'application', 'version', 'country_code', 'state', 'lifetime', 'downtime', 'availability', 'last_online_at', 'created_at', 'modified_at', 'reward_state', 'reward_time'))
    return JsonResponse(noderaw, safe=False)

@cache_memoize(10)
@require_http_methods(["GET"])
def getallNodejson(request):
    noderaw = list(PeerMonitor.objects.all().filter().values('announced_address', 'real_ip', 'platform', 'application', 'version', 'country_code', 'state', 'lifetime', 'downtime', 'availability', 'last_online_at', 'created_at', 'modified_at', 'reward_state', 'reward_time'))
    return JsonResponse(noderaw, safe=False)

@cache_memoize(300)
@require_http_methods(["GET"])
def getSNRjson(request):
    snrraw = list(PeerMonitor.objects.all().values_list('announced_address', 'real_ip', 'reward_state', 'reward_time'))
    return JsonResponse(snrraw, safe=False)
