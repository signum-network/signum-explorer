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
    IndirecIncoming,
    Trade,
    Transaction,
)

@cache_memoize(300)
@require_http_methods(["GET"])
def TopAccountsJson(request, results=10):
    bal = list(AccountBalance.objects.all().filter(latest=True,balance__gte=10000000000000).exclude(id=0).order_by('-balance').values('id', 'balance')[:results])
    return JsonResponse(bal, safe=False)

@require_http_methods(["GET"])
def getStatejson(request, address):
    state = PeerMonitor.objects.only('state').get(real_ip=address).state
    return JsonResponse(state, safe=False)

@require_http_methods(["GET"])
def getSNRjson(request):
    snrraw = list(PeerMonitor.objects.all().values_list('announced_address', 'real_ip', 'reward_state', 'reward_time'))
    return JsonResponse(snrraw, safe=False)
