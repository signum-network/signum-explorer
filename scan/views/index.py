from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from java_wallet.models import Block, Transaction
from scan.helpers.queries import get_unconfirmed_transactions_index
from scan.views.blocks import fill_data_block
from scan.views.transactions import fill_data_transaction
from django.views.decorators.csrf import csrf_protect

@csrf_protect
@cache_page(20)
def index(request):
    try:
        blocks = Block.objects.prefetch_related("id__generator_id").order_by("-height")[:5]
        txs = Transaction.objects.prefetch_related("sender_id__recipient_id__type__subtype__height__attachment_bytes").order_by("-height")[:5]
        txs_pending = get_unconfirmed_transactions_index()

        for t in txs:
            fill_data_transaction(t, list_page=True)
        
        for b in blocks:
            fill_data_block(b)
    except:
        blocks = None
        txs = None
        txs_pending = None

    context = {
        "txs": txs,
        "blocks": blocks,
        "txs_pending": txs_pending,
    }

    return render(request, "home/index.html", context)
