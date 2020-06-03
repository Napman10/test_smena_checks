# test_smena_checks
Тестовое задание для SMENA

**Примечания**
1. Для работы воркера потребуется Linux (Ubuntu) или как минимум подсистема внутри Windows.
2. Для получения нужных пакетов ввести из корня проекта в командной строке *pip install -r requirements.txt* для Windows или *pip3 install -r requirements.txt* для Linux
3. Для работы воркера потребуется Linux (Ubuntu) или как минимум подсистема внутри Windows.
4. Чтобы попасть в корень проекта из подсистемы Linux ввести *cd /mnt/PROJECT_PATH*, где PROJECT_PATH - путь к проекту

**Запуск**
1. Для начала нужно поднять инфраструктуру из PostgreSQL, Redis и Wkhtmltopdf в Docker-Compose.
Для этого в корне проекта ввести *docker-compose up* и не прерывая вводить новые команды в новых терминалах.
2. Запустить локальный сервер можно используя *python manage.py runserver* (Windows) или *python3 manage.py runserver* (Linux) из корня проекта. К этому моменту инфраструктура должна быть поднята.
3. Для запуска воркера в терминале Linux (Ubuntu) ввести *python3 manage.py rqworker default*
4. Для отмены чего-либо запущенного *Ctrl+C*

**Тестирование**
Для ввода запросов использовался Postman. Полноценно проверить метод *check* (то есть, с загрузкой pdf-файла) можно в браузере.