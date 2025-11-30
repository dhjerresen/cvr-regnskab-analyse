# xbrl_processing/arelle_loader.py

import os
from arelle import Cntlr, ModelManager, FileSource

# Path to your local taxonomy directory
TAXONOMY_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "xbrl_taxonomies"
)

def load_model(filepath: str):
    abs_path = os.path.abspath(filepath)
    cntlr = Cntlr.Cntlr(logFileName="arelle-log.txt")

    # offline mode
    cntlr.webCache.workOffline = True
    cntlr.webCache.noNetwork = True
    cntlr.webCache.recheck = 0

    model_manager = ModelManager.initialize(cntlr)

    model_xbrl = model_manager.load(
        FileSource.openFileSource(abs_path, cntlr),
        xbrlResourceDir=TAXONOMY_DIR,
        loadschemareferences=True,
        inferIxbrl=True,   # 👈 IMPORTANT
        ixbrl=True,        # 👈 IMPORTANT
        validate=False     # optional (faster)
    )

    return model_xbrl
