from django.db.models import F, OuterRef, Q
from django.views.generic import ListView

from java_wallet.models import Block, RewardRecipAssign
from scan.caching_paginator import CachingPaginator
from scan.views.pools import get_timestamp_of_block


class ForgedBlocksListView(ListView):
    model = RewardRecipAssign
    queryset = (
        RewardRecipAssign.objects.using("java_wallet")
        .filter(~Q(recip_id=F('account_id')))
        .annotate(
            block=Block.objects.using("java_wallet")
            .filter(generator_id=OuterRef("account_id"))
            .order_by("-height")
            .values("height")
            [:1]
        )
        .values("recip_id", "account_id", "block")
        .exclude(block__isnull=True)
        .exclude(recip_id__isnull=True)
        )
    template_name = "forged_blocks/list.html"
    context_object_name = "forged_blocks"
    paginator_class = CachingPaginator
    paginate_by = 25
    ordering = "-block"

    def get_queryset(self):
        qs = self.queryset
        qs = qs.filter(latest=True)
        if 'a' in self.request.GET:
            qs = qs.filter(recip_id=self.request.GET['a'], latest=1)
        return qs.order_by(self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]
        for forged_block in obj:
            forged_block["block_timestamp"] = get_timestamp_of_block(forged_block["block"])
        return context
