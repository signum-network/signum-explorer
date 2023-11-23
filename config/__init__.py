# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
#from .celery import app as celery_app

#__all__ = ("celery_app",)
from config.settings import STATIC_ROOT
from django.contrib.staticfiles.finders import BaseFinder
from pathlib import Path
import os.path, requests

STATIC_FILES = [
    {
        "url": "https://cdn.jsdelivr.net/npm/smartc-signum-decompiler/dist/index.js",
        "destination": "js/smartc-signum-decompiler/index.js",
    },
]

def download_files(destroot=None):
    if not destroot:
        destroot = os.getcwd()

    for file in STATIC_FILES:
        dir, destfile = os.path.split(file["destination"])
        destdir = os.path.join(STATIC_ROOT, dir)
        url = file["url"]

        destfile = os.path.join(destdir, destfile)
        destfile = os.path.join(destroot, destfile)

        print("Downloading %s to %s" % (url, destfile))

        if not os.path.exists(destfile):
            Path(destdir).mkdir(parents=True, exist_ok=True)

            with requests.get(url, stream=True, timeout=5) as dlwd:
                dlwd.raise_for_status()
                with open(destfile, "wb") as f:
                    for chunk in dlwd.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

class explorer_staticfiles_finder(BaseFinder):
    def list(self, ignore_patterns):
        download_files()
        return []
