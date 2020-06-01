# -*- coding: utf-8 -*-
import json
from .models import Printer, Check
from django.http import HttpResponse, JsonResponse
from wsgiref.util import FileWrapper
import requests
import base64
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django_rq import job, get_queue

def create_checks(request):
    #comm1.1 сервис получает информацию о новом заказе
    try:
        try:
            order = json.loads(request.body.decode("utf-8"))
        except TypeError:
            raise Exception("Failed to fetch")
        local_printers = Printer.objects.filter(point_id=order['point_id'])
        #comm1.4 Если у точки нет ни одного принтера - возвращает ошибку.
        if not local_printers:
            return jsonResponse({"error 400":"Для данной точки не настроено ни одного принтера"})
        #comm1.5 Если чеки для данного заказа уже были созданы - возвращает ошибку.
        existing_checks = Check.objects.filter(order=order)
        if existing_checks:
            return jsonResponse({"error 400": "Для данного заказа уже созданы чеки"})
        #comm1.2 создаёт в БД чеки для всех принтеров точки указанной в заказе
        for printer in local_printers:
            new_check = Check(printer_id=printer, ctype=printer.check_type, order=order, status="new")
            new_check.save() # ERP->API->БД
        new_checks = Check.objects.filter(order=order)
        #comm1.3 ставит асинхронные задачи на генерацию PDF-файлов для этих чеков
        queue = get_queue('default', autocommit=True, is_async=True, default_timeout=360)
        for check in new_checks:
            queue.enqueue(wkhtmltopdf, check_id=check.id)   #ERP->API->Worker->БД
        #jobs = queue.get_jobs()
        #for job in jobs:
        #    queue.remove(job)
        #    job.perform()
        #jobs = queue.get_jobs()
        # check no jobs left in queue
        #assert not jobs

        return jsonResponse({"ok":"Чеки успешно созданы"})
    except:
        return jsonResponse({"error 500": "Неизвестная ошибка"})

#comm3.1
#Приложение опрашивает сервис на наличие новых чеков.
# ~~Опрос происходит по следующему пути: 
def new_checks(api_key):
    try:
        try:
            printer_id = Printer.objects.get(api_key=api_key).id #конкретный принтер
        except:
            return jsonResponse({"error 401": "Ошибка авторизации"})
        #comm3.2 сначала запрашивается список чеков которые уже сгенерированы для конкретного принтера
        checks = Check.objects.filter(printer_id=printer_id, status='rendered')
        #comm3.3 после скачивается PDF-файл для каждого чека и отправляется на печать.
        checks_values = list(checks.values('id'))
        checks.update(status='printed')
        return jsonResponse({'checks': checks_values} )
    except:
        return jsonResponse({"error 500": "Неизвестная ошибка"} )

#отдает сгенерированный pdf для отдельного чека по апи принтера и ID чека
# в т.н. comms не входит, функция по специф
def take_pdf(api_key, check_id):
    try:
        try:
            printer_id = Printer.objects.get(api_key=api_key).id
        except:
            return jsonResponse({"error 401": "Ошибка авторизации"} )
        check = Check.objects.get(printer_id=printer_id, pk=check_id)
        if check.pdf_file:
            pdf = open(check.pdf_file.path, 'rb')
            response = HttpResponse(FileWrapper(pdf), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename={0}'.format(check.pdf_file.name)
            return response
        else:
            return jsonResponse({'error 400': "Для данного чека не сгенерирован PDF-файл"})
    except:
        return jsonResponse({"error 500": "Неизвестная ошибка"} )

@job
def wkhtmltopdf(check_id):
    check = Check.objects.get(pk=check_id)
    order_dict = {
            'items': check.order['items'],
            'address': check.order['address'],
            'order_id': check.order['id'],
            'price': check.order['price']
        }  
    if check.ctype == 'client':
        page_string_in = render_to_string('client_check.html', {**order_dict, 'client':check.order['client']})
    elif check.ctype == 'kitchen':
        page_string_in = render_to_string('kitchen_check.html', order_dict)

    page_bytes = base64.b64encode(bytes(page_string_in, 'utf-8'))
    page_string_out = page_bytes.decode('utf-8')
    #comm2.1 Асинхронный воркер с помощью wkhtmltopdf генерируют PDF-файл из HTML-шаблон
    url = 'http://127.0.0.1:80/' #http://<docker_host>:<contaimer_port>/
    data = {
        'contents': page_string_out
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

def jsonResponse(data):
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})