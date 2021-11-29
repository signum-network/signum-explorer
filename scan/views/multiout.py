from django.views.generic import ListView

from scan.caching_data.total_multiout_count import CachingTotalMultioutCount
from scan.caching_paginator import CachingPaginator
from scan.helpers.queries import get_account_name
from scan.models import MultiOut
from scan.views.filters.multiout import MultiOutFilter


def fill_data_multiouts(obj):
    obj.sender_name = get_account_name(obj.sender_id)
    if obj.recipient_id:
        obj.recipient_name = get_account_name(obj.recipient_id)

