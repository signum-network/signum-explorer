import os, json
from burst.api.brs.v1.api import BrsApi
from concurrent.futures import ThreadPoolExecutor
from config.settings import (
    SIGNUM_NODE,
    DEFAULT_P2P_PORT,
)
from dotenv import (
    load_dotenv,
    set_key,
    find_dotenv,
)
from urllib.parse import urlparse

class CachingBootstrapNodes:
    def __init__(self):
        # Use env vars (if django restarts for any reason it will re-bootstrap until manually rebooted)
        load_dotenv(override=True)
        self.auto_bootstrap_peers = os.environ.get("AUTO_BOOTSTRAP_PEERS", "False").lower() in ("true", "1", "on")
        self.brs_full_bootstrap = os.environ.get("BRS_FULL_BOOTSTRAP", "true").lower() in ("true", "1", "on")
        self.bootstrap_peers = self.get_bootstrap_peers()
        if self.auto_bootstrap_peers and self.brs_full_bootstrap:
            self.node_bootstrap()

    def get_bootstrap_peers(self):
        load_dotenv(override=True)        
        return json.loads(os.environ.get("BRS_BOOTSTRAP_PEERS", "[]"))
    
    def get_bootstrap_networks(self):
        load_dotenv(override=True)
        return tuple(json.loads(os.environ.get("BRS_BOOTSTRAP_NETWORK", '[".signum.network"]')))

    def set_bootstrap_peers(self, peers):
        set_key(dotenv_path=find_dotenv(), key_to_set="BRS_BOOTSTRAP_PEERS", value_to_set=(json.dumps(peers)), export=False, quote_mode="never")

    def explore_peer(self, peer, bootstrap, networks):
        try:
            url = urlparse(BrsApi(SIGNUM_NODE).get_peer(peer)['announcedAddress'])
            if not url: raise Exception("No URL Found") # Debug info only
            if int(url.path) == DEFAULT_P2P_PORT: announced = url.scheme
            elif url.path: announced = f"{url.scheme}:{url.path}"
            else: raise Exception("No Announced Address")
        except: 
            return
        else:
            for network in networks:
                if announced.endswith(network):
                    bootstrap.add(announced)
                    break
            return

    ## VERY SLOW, AND HARD ON NODE ##
    # ONLY RUN ONCE AT FIRST STARTUP #
    def node_bootstrap(self):
        print("Running First Time Node Bootstrap...\nThis will take a while and is a blocking function.\nIf this is not needed restart the node with BRS_FULL_BOOTSTRAP=False")

        try:
            peers = BrsApi(SIGNUM_NODE).get_peers()
            bootstrap = set(self.get_bootstrap_peers()) # your own node won't be in the list so load prespecified peers
            networks = self.get_bootstrap_networks()

            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(lambda peer: self.explore_peer(peer, bootstrap, networks), peers)
                
        except Exception as e:
            print(f"Failed to get bootstrap peers from node: {e}")
        else:
            try:
                self.set_bootstrap_peers(list(bootstrap))
            except Exception as e:
                print(f"Failed to update Bootstrap Peers: {e}")
            else:
                try:
                    set_key(dotenv_path=find_dotenv(), key_to_set="BRS_FULL_BOOTSTRAP", value_to_set="off", export=False, quote_mode="never")
                except Exception as e:
                    print(f"Failed to disable next full bootstrap run: \n{e}\n\nIf the peers are now in your env, you should add BRS_FULL_BOOTSTRAP=False now")
                else:
                    print(f"Bootstrap Peers: {bootstrap}")
