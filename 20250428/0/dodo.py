from pathlib import Path

DOIT_CONFIG = {"default_tasks": ["docs"]}
DOCZIP = "docs.zip" 
DOCLIST = "docs.list"

def task_zip():
    return {
            "task_dep": ["docs"], 
            "actions": ["zip -r docs.zip _build/html"],
            "targets": [DOCZIP],
    }

def task_docs():
    """Build documentation"""
    return {
        "file_dep": [
            *Path("source").glob("*.rst"),
            *Path("source").glob("*.py"),
            *Path("restcalend").glob("*.py"),
        ],
        "actions": ["sphinx-build -M html source build"],
        "targets": ["build"],
    }

def task_stat():
    return {
            "file_dep": [DOCZIP],
            "targets": [DOCLIST],
            "actions": [(list_zip, [DOCZIP, DOCLIST])],
            }

def task_erase():
    """Erase all generated files"""
    return {
        "actions": ["git clean -fdx"],
    }

def list_zip(name, outfile):
    with ZipFile(name) as zf:
        res = zf.namelist()
    with open(outfile, "w") as of:
        print("\n".join(res), file=of)
