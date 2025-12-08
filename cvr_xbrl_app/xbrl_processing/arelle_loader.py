# xbrl_processing/arelle_loader.py

import os
import re
import pathlib
from arelle import Cntlr, ModelManager, FileSource

# path to your taxonomy directory
TAXONOMY_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "xbrl_taxonomies"
)

# Fix for old archprod taxonomy references
def fix_schema_refs(xml_text: str, taxonomy_dir: str) -> str:
    """
    Replace ANY archprod schemaRef with your local 20241001 entrypoint.
    Works for all years.
    """

    archprod_pattern = re.compile(
        r"http://archprod\.service\.eogs\.dk/taxonomy/\d{8}/entry[^\"']+\.xsd"
    )

    # ALWAYS map old archprod files to NEW local entrypoint (20241001)
    local_entry = (
        pathlib.Path(taxonomy_dir)
        / "20241001"
        / "entryDanishGAAPBalanceSheetAccountFormIncomeStatementByNatureIncludingManagementsReviewStatisticsAndTax20241001.xsd"
    )

    new_url = "file://" + str(local_entry.resolve())

    # replace every match
    xml_text = archprod_pattern.sub(new_url, xml_text)

    return xml_text

# Loader
def load_model(filepath: str):
    abs_path = os.path.abspath(filepath)

    # Read and patch XBRL instance BEFORE Arelle touches it
    with open(abs_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    xml_text = fix_schema_refs(xml_text, TAXONOMY_DIR)

    # write patched file as temp
    patched = abs_path + ".patched"
    with open(patched, "w", encoding="utf-8") as f:
        f.write(xml_text)

    # Arelle setup
    cntlr = Cntlr.Cntlr(logFileName="arelle-log.txt")
    cntlr.webCache.workOffline = True
    cntlr.webCache.noNetwork = True
    cntlr.webCache.recheck = 0

    model_manager = ModelManager.initialize(cntlr)

    model_xbrl = model_manager.load(
        FileSource.openFileSource(patched, cntlr),
        xbrlResourceDir=TAXONOMY_DIR,
        loadschemareferences=True,
        inferIxbrl=True,
        ixbrl=True,
        validate=False
    )

    return model_xbrl
