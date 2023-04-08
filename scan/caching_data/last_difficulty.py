from java_wallet.models import Block
from scan.caching_data.base import CachingDataBase


class CachingCumulativeDifficulty(CachingDataBase):
    _cache_key = "last_cumulative_difficulty"
    _cache_expiring = 0
    live_if_empty = True
    default_data_if_empty = None

    def _get_live_data(self):
        result = str(int((
            Block.objects.using("java_wallet")
            .order_by("-height")
            .values("cumulative_difficulty")
            .first()
        )["cumulative_difficulty"].hex(), 16))
        return result