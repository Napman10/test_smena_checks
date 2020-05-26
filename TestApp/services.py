import json
import django_rq
from .models import Printer, Check
from django.http import HttpResponse, JsonResponse
from wsgiref.util import FileWrapper
import requests
import base64
from django.template.loader import render_to_string
from django.core.files.base import ContentFile

def create_checks(order):
    #comm1.1 сервис получает информацию о новом заказе
    order = json.loads(order)
    local_printers = Printer.objects.filter(point_id=order['point_id'])
    #comm1.4 Если у точки нет ни одного принтера - возвращает ошибку.
    if not local_printers:
        return JsonResponse({"error":"Для данной точки не настроено ни одного принтера"}, status=400)
    #comm1.5 Если чеки для данного заказа уже были созданы - возвращает ошибку.
    existing_checks = Check.objects.filter(order=order)
    if existing_checks:
        return JsonResponse({"error": "Для данного заказа уже созданы чеки"}, status=400)
    new_checks = list()
    #comm1.2 создаёт в БД чеки для всех принтеров точки указанной в заказе
    for printer in local_printers:
        new_check = Check(printer_id=printer, ctype=printer.check_type, order=order, status="new")
        new_check.save() # ERP->API->БД
        new_checks.append(new_check)
    #comm1.3 ставит асинхронные задачи на генерацию PDF-файлов для этих чеков
    wkhtmltopdf(new_checks[0].id)
    for check in new_checks:
        django_rq.enqueue(wkhtmltopdf, check_id=check.id)   #ERP->API->Worker->БД
    if new_checks:
        return JsonResponse({"ok": 'Чеки успешно созданы'}, status=200)
    return JsonResponse({"error": "Неизвестная ошибка"}, status=500)

#comm3.1
#Приложение опрашивает сервис на наличие новых чеков.
# ~~Опрос происходит по следующему пути: 
def new_checks(api_key):
    try:
        printer_id = Printer.objects.filter(api_key=api_key)[0].id #конкретный принтер
        #comm3.2 сначала запрашивается список чеков которые уже сгенерированы для конкретного принтера
        checks = Check.objects.filter(printer_id=printer_id, status='rendered').values('id')
        #comm3.3 после скачивается PDF-файл для каждого чека и отправляется на печать. (???????, не факт что правильно)
        #здесь нужно лаконично поменять таким чекам статус rendered->printed
        return JsonResponse({'checks': list(checks)}, status=200)
    except IndexError:
        return JsonResponse({"error": "Ошибка авторизации"}, status=401)
    except:
        return JsonResponse({"error": "Неизвестная ошибка"}, status=500)

#отдает сгенерированный pdf для отдельного чека по апи принтера и ID чека
# в т.н. comms не входит, функция по специф
def take_pdf(api_key, check_id):
    try:
        printer_id = Printer.objects.filter(api_key=api_key)[0].id
        check = Check.objects.get(printer_id=printer_id, pk=check_id)
        if check.pdf_file:
            pdf = open(check.pdf_file.path, 'rb')
            content_type = 'application/pdf'
            response = HttpResponse(FileWrapper(pdf), content_type=content_type)
            response['Content-Disposition'] = 'attachment; filename=%s' % check.pdf_file.name
            return response
        else:
            return JsonResponse({'error': "Для данного чека не сгенерирован PDF-файл"}, status=400)
    except IndexError:
        return JsonResponse({"error": "Ошибка авторизации"}, status=401)
    except:
        return JsonResponse({"error": "Неизвестная ошибка"}, status=500)

def wkhtmltopdf(check_id):
    page = None
    check = Check.objects.get(pk=check_id)
    if check.ctype == 'client':
        page = render_to_string('client_check.html', {
            'items': check.order['items'],
            'client': check.order['client'],
            'address': check.order['address'],
            'order_id': check.order['id'],
            'price': check.order['price']
        })
    elif check.ctype == 'kitchen':
        page = render_to_string('kitchen_check.html', {
            'items': check.order['items'],
            'address': check.order['address'],
            'order_id': check.order['id'],
            'price': check.order['price']
        })
    b = base64.b64encode(bytes(page, 'utf-8'))
    data_contents = b.decode('utf-8')
    #comm2.1 Асинхронный воркер с помощью wkhtmltopdf генерируют PDF-файл из HTML-шаблон
    url = 'http://127.0.0.1:80/' #http://<docker_host>:<contaimer_port>/
    data = {
        #'contents': converted_html, #здесь должен быть пережитый обработку html
        'contents': data_contents
    }
    headers = {
        'Content-Type': 'application/json',    # This is important ===> не менять
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    content = ContentFile(response.content)
    #comm2.2 Имя файла должно иметь следущий вид <ID заказа>_<тип чека>.pdf (123456_client.pdf)
    #comm2.3 в модели чека
    file_name = "{0}_{1}.pdf".format(check.order["id"], check.ctype)
    check.pdf_file.save(file_name, content, True)
    check.status = 'rendered'
    check.save()
    