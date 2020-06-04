# test_smena_checks
Тестовое задание для SMENA

**Примечания**
1. Для работы воркера потребуется Linux (Ubuntu) или как минимум подсистема внутри Windows.
2. Для получения нужных пакетов ввести *pip install -r requirements.txt*
3. Чтобы попасть в корень проекта из подсистемы Linux ввести *cd /mnt/PROJECT_PATH*, где PROJECT_PATH - путь к проекту
4. Для Linux вместо *python* и *pip* вводить *python3* и *pip3*

**Запуск**
1. Поднять инфраструктуру из PostgreSQL, Redis и Wkhtmltopdf в Docker-Compose.
Для этого в корне проекта ввести *docker-compose up* и не прерывая вводить новые команды в новых терминалах.
2. Выполнить миграцию введя *python manage.py migrate*
3. Для загрузки начальных данных о принтерах ввести *python manage.py loaddata fixtures/fixture1.json*
4. Запустить локальный сервер введя *python manage.py runserver*. К этому моменту инфраструктура должна быть поднята.
5. Для запуска воркера в терминале Linux (Ubuntu) ввести *python3 manage.py rqworker default*

**Тестирование**

Для ввода запросов использовался Postman. Полноценно проверить метод *check* (то есть, с загрузкой pdf-файла) можно в браузере.
