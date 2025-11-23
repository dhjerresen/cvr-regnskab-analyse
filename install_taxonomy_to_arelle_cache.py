import os
import shutil

# Local folder where you unpacked the XBRL taxonomy
LOCAL_TAXONOMY_ROOT = "/Users/danielhjerresen/Library/CloudStorage/Dropbox/Uni/Data-driven_business_model/Semester_project/xbrl_taxonomy/XBRL20241001/20241001"

# Arelle cache root
ARELLE_CACHE = "/Users/danielhjerresen/Library/Caches/Arelle/http/archprod.service.eogs.dk/taxonomy/20241001"

def copy_taxonomy():
    print("Local taxonomy:", LOCAL_TAXONOMY_ROOT)
    print("Arelle cache target:", ARELLE_CACHE)

    # Create the base directory (matching Arelle's expected structure)
    os.makedirs(ARELLE_CACHE, exist_ok=True)

    # Recursively copy everything
    for root, dirs, files in os.walk(LOCAL_TAXONOMY_ROOT):
        rel = os.path.relpath(root, LOCAL_TAXONOMY_ROOT)
        dest_dir = os.path.join(ARELLE_CACHE, rel)
        os.makedirs(dest_dir, exist_ok=True)

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(dest_dir, f)
            shutil.copy2(src, dst)

    print("\n✔ Taxonomy copied into Arelle cache exactly where Arelle looks for it.")
    print("You can now load test.xml in offline mode with NO missing schemas.")

if __name__ == "__main__":
    copy_taxonomy()
