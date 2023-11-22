import os, json, socket, requests
#from burst.api.brs.p2p import P2PApi
from concurrent.futures import ThreadPoolExecutor
from config.settings import (
    SIGNUM_NODE,
    BRS_BOOTSTRAP_NETWORK,
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

    def set_bootstrap_peers(self, peers):
        set_key(dotenv_path=find_dotenv(), key_to_set="BRS_BOOTSTRAP_PEERS", value_to_set=(json.dumps(peers)), export=False, quote_mode="never")

    def explore_peer(self, peer, address, bootstrap):
        try:
            announced = (
                urlparse(
                    requests.get(f"{address}/burst?requestType=getPeer&peer={peer}").json()['announcedAddress']
                ).scheme # apparently node returns address in scheme instead of http/https
            )
            if not announced: raise Exception("No Announced Address") # Debug info only
        except: 
            return
        else:
            if announced.endswith((BRS_BOOTSTRAP_NETWORK)):
                bootstrap.add(announced)
            return

    ## VERY SLOW, AND HARD ON NODE ##
    # ONLY RUN ONCE AT FIRST STARTUP #
    def node_bootstrap(self):
        print("Running First Time Node Bootstrap...\nThis will take a while and is a blocking function.\nIf this is not needed restart the node with BRS_FULL_BOOTSTRAP=False")
        """
            Requests doesn't have docker/container lookup  
            use urlparse to get the node url(hostname)  
            followed by socket to get the IP address  
            then find the bootstrap network peers to use
        """

        try:
            local_node = urlparse(SIGNUM_NODE)
            host = socket.gethostbyname(f'{local_node.hostname}')
            address = f'{local_node.scheme}://{host}:{local_node.port}'
            #peers = P2PApi(str(f'{host}:8125')).get_peers() ## API doesn't work if using cloudflare direct request required
            peers = list(set(requests.get(f"{address}/burst?requestType=getPeers").json()['peers']))
            
            bootstrap = set()

            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(lambda peer: self.explore_peer(peer, address, bootstrap), peers)
                
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
