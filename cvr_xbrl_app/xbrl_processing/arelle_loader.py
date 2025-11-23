# xbrl_processing/arelle_loader.py
import os
from arelle import Cntlr, ModelManager, FileSource

def load_model(filepath: str):
    """
    Load an XBRL or Inline XBRL file using Arelle in offline mode.
    Returns an Arelle modelXbrl object.
    """
    cntlr = Cntlr.Cntlr(logFileName="arelle-log.txt")

    # Allow Arelle to download taxonomy definitions referenced by filings
    cntlr.webCache.workOffline = False
    cntlr.webCache.recheck = 0
    cntlr.webCache.noCertificateCheck = True

    model_manager = ModelManager.initialize(cntlr)

    abs_path = os.path.abspath(filepath)
    model_xbrl = model_manager.load(FileSource.openFileSource(abs_path, cntlr))

    return model_xbrl
