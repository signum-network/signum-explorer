import os, json
from dotenv import (
    load_dotenv,
    set_key,
    find_dotenv,
)

class CachingBootstrapNodes:
    def __init__(self):
        self.bootstrap_peers = self.get_bootstrap_peers()

    def get_bootstrap_peers(self):
        load_dotenv(override=True)        
        return json.loads(os.environ.get("BRS_BOOTSTRAP_PEERS", "[]"))

    def set_bootstrap_peers(self, peers):
        set_key(dotenv_path=find_dotenv(), key_to_set="BRS_BOOTSTRAP_PEERS", value_to_set=(json.dumps(peers)), export=False, quote_mode="never")
