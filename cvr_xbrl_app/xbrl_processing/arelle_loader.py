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
    """
    Universal loader for XML/XBRL/iXBRL/ESEF XHTML.
    Forces Arelle to use local taxonomies.
    """

    abs_path = os.path.abspath(filepath)
    cntlr = Cntlr.Cntlr(logFileName="arelle-log.txt")

    # Use ONLY local taxonomies
    cntlr.webCache.workOffline = True
    cntlr.webCache.noNetwork = True
    cntlr.webCache.recheck = 0

    model_manager = ModelManager.initialize(cntlr)

    model_xbrl = model_manager.load(
        FileSource.openFileSource(abs_path, cntlr),
        xbrlResourceDir=TAXONOMY_DIR,
        loadschemareferences=True
    )

    return model_xbrl
