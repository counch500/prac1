Запуск сервера:
pipenv run python -m mood.server
mood-server

Запуск клиента:
pipenv run python -m mood.client <ИМЯ>
PYTHONPATH=src python -m mood.client ll
mood-client

Локализация:
Переводы хранятся в папке src/mood/locales.

Загрузка пакета:
1. Установка нового окружения(cowsay, sphinx, doit, babel)
2. Загрузка пакета через: 
 pipenv install $(pwd)/dist/mood-1.0.0-py3-none-any.whl

Создание wheel/sdist:
doit wheel/sdist
+doit html/i18l

Проверка установки пакета в трёх чистых окружениях:
source venv_server/bin/activate
pip install .
deactivate

source venv_client1/bin/activate
pip install .
deactivate

source venv_client2/bin/activate
pip install .
deactivate

Тестирование с файлом:
mood-client tetsus --file cmd.mood

Тестирование с юниттестами(клиент и сервер):
python -m unittest tests/test_server.py
python -m unittest tests/test_client.py