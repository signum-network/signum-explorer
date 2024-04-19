from django.db.models import Q
from django_filters import FilterSet, NumberFilter, CharFilter
from burst.libs.reed_solomon import ReedSolomon, ReedSolomonError
from java_wallet.models import IndirectIncoming, Transaction, Account

import os


class TxFilter(FilterSet):
    block = NumberFilter(field_name="block__height")
    blk = NumberFilter(field_name="block__height")
    a = NumberFilter(method="filter_by_account")
    has_message = NumberFilter(field_name="has_message")
    type = NumberFilter(field_name="type")
    subtype = NumberFilter(field_name="subtype")
    id = NumberFilter(field_name="id")
    amount = NumberFilter(field_name="amount", method="scale_amount")
    sender_id = CharFilter(field_name="sender_id", method="rs_id")
    recipient_id = CharFilter(field_name="recipient_id", method="rs_id")
    tst = CharFilter(method="tx_type_subtype")
       
    class Meta:
        model = Transaction
        fields = ("block", "a", "has_message", "type", "subtype", "id", "amount", "sender_id", "recipient_id")
   
    def rs_id(self, queryset, name, value):
        try:
            if value.startswith(os.environ.get("ADDRESS_PREFIX")):
                value = value[len(os.environ.get("ADDRESS_PREFIX")):]
                numeric_id = ReedSolomon().decode(value)
                return queryset.filter(**{name: numeric_id})
            elif value.isdigit():
                return queryset.filter(**{name: value})
            else:
                account_exists = (
                    Account.objects.using("java_wallet")
                    .filter(name=value).exists()
                )
                if account_exists:
                    act_name = (
                        Account.objects.using("java_wallet")
                        .filter(name=value)
                        .order_by("-height")
                        .values_list("id", flat=True)
                        .first()
                    )
                    return queryset.filter(**{name: act_name})
                else:
                    return queryset.filter(**{name: '000'})

        except:
            return queryset.filter(**{name: '000'})
        
    def tx_type_subtype(self, queryset, name, value):
        try:
            type_value, subtype_value = map(int, value.split('_'))
            queryset = queryset.filter(type=type_value, subtype=subtype_value)
        except: 
            queryset = queryset.filter(type=value)
        return queryset

    def scale_amount(self, queryset, name, value):
        return queryset.filter(**{name: value * 100000000})

    @staticmethod
    def filter_by_account(queryset, name, value):
        indirects = list(
            IndirectIncoming.objects.using("java_wallet")
            .values_list('transaction_id', flat=True)
            .filter(account_id=value)
        )
        return queryset.filter(Q(sender_id=value) | Q(recipient_id=value) | Q(id__in=indirects))
 
    def filter_by_indirects(queryset, name, value):
        indirects = list(
            IndirectIncoming.objects.using("java_wallet")
            .values_list('db_id', flat=True)
            .filter(transaction_id=value)
        )
        return queryset.filter(Q(id__in=indirects))
