import json
import django_rq
from .models import Printer, Check
from django.http import HttpResponse, JsonResponse
from wsgiref.util import FileWrapper
import requests
import base64

def create_checks(order):
    order = json.loads(order)
    local_printers = Printer.objects.filter(point_id=order['point_id'])

    if not local_printers:
        return JsonResponse({"error":"Для данной точки не настроено ни одного принтера"}, status=400)

    checks = Check.objects.filter(printer_id__in=local_printers.values('pk'), order=order)
    printers = local_printers.exclude(pk__in=checks.values('printer_id__pk'))

    if checks and not printers:
        return JsonResponse({"error": "Для данного заказа уже созданы чеки"}, status=400)

    if printers:
        for p in local_printers:
            new_check = Check(printer_id=p, ctype=p.check_ctype, order=order)
            new_check.save()
        check_list = Check.objects.all()

        for c in check_list:
            django_rq.enqueue(pdf_worker, c)
        
        if check_list:
            return JsonResponse({"ok": "Чеки успешно созданы"}, status=200)

    return JsonResponse({"error": "Неизвестная ошибка"}), status=500
        
def take_available_checks(api_key):
    #получаем принтеры по ключу
    printer_id = Printer.objects.filter(api_key=api_key)[0].id
    #получаем чеки
    ab_checks = Check.objects.filter(printer_id=printer_id, status='rendered')
    return ab_checks
    
def take_pdf(api_key, check_id):
    printer_id = Printer.objects.filter(api_key=api_key)[0].id
    check = Check.objects.get(printer_id=printer_id, pk=check_id)
    pdf = open(check.pdf_file.path, 'rb')
    content_type = 'application/pdf'
    response = HttpResponse(FileWrapper(pdf), content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % check.pdf_file.name
    return response
    
def pdf_worker(check_id):
    #получить чек
    page = None
    check = Check.objects.get(pk=check_id)
    #обработать для двух разных случаев
    if check.ctype == "client":
        #инструкции
        pass
    if check.ctype == "kitchen":
        #инструкции
        pass
    #после этого convert_html стал строкой
    b = page.encode("utf-8")
    converted_html = base64.b64encode(b)
    url = 'http://127.0.0.1:80/'
    data = {
        'contents': converted_html, #здесь должен быть пережитый обработку html
    }
    headers = {
        'Content-Type': 'application/json',    # This is important ===> не менять
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    # Тут пока неизвестно
    with open('/path/to/local/file.pdf', 'wb') as f:
        f.write(response.content)
    #доделать обработку и сохранение
    
    