import shutil
from pathlib import Path
from doit.tools import create_folder

DOIT_CONFIG = {'default_tasks': ['html']}

def task_pot():
    """Extract gettext messages to .pot"""
    return {
        'actions': ['pybabel extract -o mood/locale/mud.pot mood'],
        'targets': ['mood/locale/mud.pot'],
        'clean': True,
    }

def task_po():
    """Update .po from .pot"""
    return {
        'actions': ['pybabel update -i mood/locale/mud.pot -d mood/locale -D mud -l ru_RU.UTF-8'],
        'file_dep': ['mood/locale/mud.pot'],
        'targets': ['mood/locale/ru_RU.UTF-8/LC_MESSAGES/mud.po'],
        'clean': True,
    }

def task_mo():
    """Compile .po to .mo"""
    return {
        'actions': ['pybabel compile -d mood/locale -D mud'],
        'file_dep': ['mood/locale/ru_RU.UTF-8/LC_MESSAGES/mud.po'],
        'targets': ['mood/locale/ru_RU.UTF-8/LC_MESSAGES/mud.mo'],
        'clean': True,
    }

def task_i18n():
    """Full i18n pipeline"""
    return {
        'actions': None,
        'task_dep': ['pot', 'po', 'mo'],
    }

def task_html():
    """Build HTML docs"""
    source_dir = Path("docs/source")
    build_dir = Path("docs/build")
    html_dir = build_dir / "html"

    return {
        'actions': ['sphinx-build -M html docs/source docs/build'],
        'file_dep': list(map(str, source_dir.glob('*.rst'))) + ['docs/source/conf.py'],
        'targets': [str(html_dir / 'index.html')],
        'clean': [(shutil.rmtree, [str(html_dir)])],
    }

def task_test():
    """Run pytest (with translations)"""
    return {
        'actions': ['python -m unittest discover -s tests'],
        'task_dep': ['i18n'],
    }
