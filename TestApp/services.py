import json
import django_rq
from .models import Printer, Check
from django.http import HttpResponse, JsonResponse
from wsgiref.util import FileWrapper
import requests
import base64
from django.template.loader import render_to_string

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
    return JsonResponse({"error": "Неизвестная ошибка"}, status=500)
        
def take_available_checks(api_key):
    try:
        printer_id = Printer.objects.filter(api_key=api_key)[0].id
        ab_checks = Check.objects.filter(printer_id=printer_id, status='rendered')
        return JsonResponse({'checks': list(ab_checks)}, status=200)
    except IndexError:
        return JsonResponse({"error": "Ошибка авторизации"}, status=401)
    except:
        return JsonResponse({"error": "Неизвестная ошибка"}, status=500)
    
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
    
def pdf_worker(check_id):
    #получить чек
    page = None
    check = Check.objects.get(pk=check_id)
    #обработать для двух разных случаев
    if check.ctype == "client":
        context = dict()
        page = render_to_string("client_check.html", context)
    if check.ctype == "kitchen":
        context = dict()
        page = render_to_string("kitchen_check.html", context)
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
    file_name = "{0}_{1}.pdf".format(check.order["id"], check.type)
    check.pdf_file.save(file_name, response.content, True)
    check.save()
    