Запуск сервера
pipenv run python -m mood.server

Запуск клиента
pipenv run python -m mood.client <ИМЯ>
PYTHONPATH=src python -m mood.client ll

Локализация
Переводы хранятся в папке src/mood/locales.

Загрузка пакета:
1. Установка нового окружения(cowsay, sphinx, doit, babel)
2. Загрузка пакета через: 
 pipenv install $(pwd)/dist/mood-1.0.0-py3-none-any.whl

Создание wheel/sdist
doit wheel/sdist