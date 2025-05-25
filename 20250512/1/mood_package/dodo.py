import shutil
from pathlib import Path
from doit.tools import create_folder

DOIT_CONFIG = {'default_tasks': ['html']}

def task_html():
    """Собрать HTML-документацию"""
    source_dir = Path("src/mood/docs/source")
    build_dir = Path("src/mood/docs/build")
    html_dir = build_dir / "html"

    return {
        'actions': [
            (create_folder, [str(build_dir)]),
            'sphinx-build -M html src/mood/docs/source src/mood/docs/build'
        ],
        'file_dep': list(map(str, source_dir.glob('*.rst'))) + ['src/mood/docs/source/conf.py'],
        'targets': [str(html_dir / 'index.html')],
        'uptodate': [False],  # <- ДОБАВЬ ЭТО
        'clean': [(shutil.rmtree, [str(html_dir)])],
    }

def task_sdist():
    """Собрать исходный дистрибутив (sdist)"""
    return {"actions": ["python -m build --sdist"]}

def task_wheel():
    """Собрать wheel-дистрибутив"""
    return {"actions": ["python -m build --wheel"]}

def task_build():
    """Собрать и sdist, и wheel"""
    return {
        'actions': ['python -m build'],
        'file_dep': ['pyproject.toml', 'MANIFEST.in'],
        'targets': ['dist/'],
    }

def task_pot():
    """Извлечь сообщения в .pot-файл"""
    return {
        'actions': ['pybabel extract -o src/mood/locales/mud.pot src/mood'],
        'targets': ['src/mood/locales/mud.pot'],
        'clean': True,
    }

def task_po():
    """Обновить .po-файл из .pot"""
    return {
        'actions': [
            'pybabel update -i src/mood/locales/mud.pot -d src/mood/locales -D mud -l ru_RU'
        ],
        'file_dep': ['src/mood/locales/mud.pot'],
        'targets': ['src/mood/locales/ru_RU/LC_MESSAGES/mud.po'],
        'clean': True,
    }

def task_mo():
    """Скомпилировать .po в .mo"""
    return {
        'actions': ['pybabel compile -d src/mood/locales -D mud'],
        'file_dep': ['src/mood/locales/ru_RU/LC_MESSAGES/mud.po'],
        'targets': ['src/mood/locales/ru_RU/LC_MESSAGES/mud.mo'],
        'clean': True,
    }


def task_i18n():
    """Полный цикл i18n"""
    return {
        'actions': None,
        'task_dep': ['pot', 'po', 'mo'],
    }

def task_test():
    """Прогнать юнит-тесты"""
    return {
        'actions': ['python -m unittest discover -s tests'],
        'task_dep': ['i18n'],
    }
