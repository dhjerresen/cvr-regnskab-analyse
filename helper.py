import os
import shutil
from pathlib import Path

local_taxonomy = Path("/Users/danielhjerresen/Library/CloudStorage/Dropbox/Uni/Data-driven_business_model/Semester_project/xbrl_taxonomy/XBRL20241001/20241001")

cache_root = Path(os.environ.get("HOME")) / ".arelle" / "cache" / "http" / "archprod.service.eogs.dk" / "taxonomy" / "20241001"

cache_root.mkdir(parents=True, exist_ok=True)

# Copy all taxonomy files into the cache
for item in local_taxonomy.rglob("*"):
    dest = cache_root / item.relative_to(local_taxonomy)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if item.is_file():
        shutil.copy2(item, dest)

print("Taxonomy copied into Arelle cache.")
