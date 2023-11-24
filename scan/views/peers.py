from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView
from scan.caching_data.bootstrap_nodes import CachingBootstrapNodes
from django.http import HttpResponse
from scan.models import PeerMonitor

caching_peers = CachingBootstrapNodes()

@require_http_methods(["GET"])
def peers_charts_view(request):
    online_now = PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE).count()
    versions = (
        PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE)
        .values("version")
        .annotate(cnt=Count("version"))
        .order_by("-version", "-cnt")
    )
    
    votes = (
        PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE).exclude(reward_state='Duplicate')
        .values("platform")
        .annotate(cnt=Count("platform"))
        .order_by("-cnt")
    )
        
    countries = (
        PeerMonitor.objects.filter(state=PeerMonitor.State.ONLINE)
        .values("country_code")
        .annotate(cnt=Count("country_code"))
        .order_by("-cnt", "country_code")
    )

    states = (
        PeerMonitor.objects.values("state")
        .annotate(cnt=Count("state"))
        .order_by("-cnt", "state")
    )
    for state in states:
        state["state"] = PeerMonitor(state=state["state"]).get_state_display()

    last_check = (
        PeerMonitor.objects.values("modified_at").order_by("-modified_at").first()
    )

    return render(
        request,
        "peers/charts.html",
        {
            "online_now": online_now,
            "versions": versions,
            "countries": countries,
            "states": states,
            "last_check": last_check,
            "votes": votes,
        },
    )


class PeerMonitorListView(ListView):
    model = PeerMonitor
    queryset = PeerMonitor.objects.all()
    template_name = "peers/list.html"
    context_object_name = "peers"
    paginate_by = 200
    ordering = ("-version", "state", "-availability", "announced_address")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        featured_peers = (
            PeerMonitor.objects
            .filter(announced_address__in=caching_peers.get_bootstrap_peers())
            .filter(state=1)
            .order_by("-version", "-availability")
        )

        context["featured_peers"] = featured_peers

        return context


class PeerMonitorDetailView(DetailView):
    model = PeerMonitor
    queryset = PeerMonitor.objects.all()
    template_name = "peers/detail.html"
    context_object_name = "peer"
    slug_field = "announced_address"
    slug_url_kwarg = "address"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context[self.context_object_name]

        if obj.state == 3 or obj.state == 4: # 4 could be removed if we only want sync
            featured_peers = []
            bootstrap_peers = caching_peers.get_bootstrap_peers()
            for peer in bootstrap_peers:
                featured_peer = PeerMonitor.objects.filter(announced_address=peer).exclude(state__gt=1).values("height").first()
                if featured_peer:
                    featured_peers.append(featured_peer["height"])

            context["concensus"] = round(sum(featured_peers)/len(featured_peers))
            context["progress"] = str(round((obj.height / context["concensus"]) * 100, 2))

        return context
