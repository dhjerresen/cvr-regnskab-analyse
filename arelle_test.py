import os
from arelle import Cntlr, ModelManager, FileSource

def load_xbrl(filename):
    # Create controller with NO INTERNET
    cntlr = Cntlr.Cntlr(logFileName="logToPrint")

    # Force offline mode the only way supported in your macOS build:
    cntlr.webCache.workOffline = True
    cntlr.webCache.recheck = 0
    cntlr.webCache.noCertificateCheck = True

    # Create model manager
    model_manager = ModelManager.initialize(cntlr)

    # Load file
    filepath = os.path.abspath(filename)
    print("Loading:", filepath)

    model_xbrl = model_manager.load(FileSource.openFileSource(filepath, cntlr))
    return model_xbrl


def print_facts(model_xbrl):
    print("\n===== FACTS =====\n")
    for fact in model_xbrl.facts:
        if fact.value not in ("", None):
            print(f"{fact.qname}: {fact.value}")

def get_revision_type(model_xbrl):
    """Return the value of the TypeOfAuditorAssistance fact if it exists."""
    for fact in model_xbrl.facts:
        if fact.qname.localName == "TypeOfAuditorAssistance" and fact.value not in ("", None):
            return fact.value
    return None

if __name__ == "__main__":
    model = load_xbrl("test.xml")
    revision_type = get_revision_type(model)
    print(f"Type of revision: {revision_type}" if revision_type else "Type of revision not found")
    print_facts(model)
