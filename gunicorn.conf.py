# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing
from dotenv import load_dotenv
load_dotenv()

bind = "0.0.0.0:5000"
worker_class = "gthread"
workers = max(2, multiprocessing.cpu_count() * 2)
#threads = 3 * multiprocessing.cpu_count()
threads = 4
timeout = 120
graceful_timeout = 30
keepalive = 5
max_requests = 2000
max_requests_jitter = 300
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
loglevel = "info"
