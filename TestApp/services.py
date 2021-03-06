import json
from .models import Printer, Check
from django.http import HttpResponse, JsonResponse
from wsgiref.util import FileWrapper
import requests
from base64 import b64encode
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django_rq import job, get_queue
from django.core.exceptions import ObjectDoesNotExist
#решает проблему с кириллицей в JsonResponse
def jsonResponse(data, status):
    return JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False}, status=status)

def create_checks(request):
    try:
        order = json.loads(request.body.decode("utf-8"))    
        local_printers = Printer.objects.filter(point_id=order['point_id'])

        if not local_printers:
            return jsonResponse({"error":"Для данной точки не настроено ни одного принтера"}, 400)

        existing_checks = Check.objects.filter(order=order)
        if existing_checks:
            return jsonResponse({"error": "Для данного заказа уже созданы чеки"}, 400)

        for printer in local_printers:
            new_check = Check(printer_id=printer, ctype=printer.check_type, order=order, status="new")
            new_check.save() 

        new_checks = Check.objects.filter(order=order)

        queue = get_queue('default', autocommit=True, is_async=True, default_timeout=360)
        for check in new_checks:
            queue.enqueue(wkhtmltopdf, check_id=check.id)

        return jsonResponse({"ok":"Чеки успешно созданы"}, 200)

    except:
        return jsonResponse({"error":"Неизвестная ошибка"}, 500)


def new_checks(api_key):
    try:
        printer_id = Printer.objects.get(api_key=api_key).id 
        checks = Check.objects.filter(printer_id=printer_id, status='rendered')

        checks_values = list(checks.values('id'))

        return jsonResponse({'checks': checks_values}, 200 )

    except ObjectDoesNotExist:
        return jsonResponse({"error": "Ошибка авторизации"}, 401)

    except:
        return jsonResponse({"error":"Неизвестная ошибка"}, 500)

def check(api_key, check_id):
    try:
        printer_id = Printer.objects.get(api_key=api_key).id       
        check = Check.objects.get(printer_id=printer_id, pk=check_id)

        if check.pdf_file:           
            pdf = open(check.pdf_file.path, 'rb')

            response = HttpResponse(FileWrapper(pdf), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename={0}'.format(check.pdf_file.name)

            check.status = 'printed'
            check.save()

            return response

        else:
            return jsonResponse({'error': "Для данного чека не сгенерирован PDF-файл"}, 400)      

    except ObjectDoesNotExist:
            return jsonResponse({"error": "Ошибка авторизации"}, 401 )

    except:
        return jsonResponse({"error":"Неизвестная ошибка"}, 500)

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

    page_bytes = b64encode(bytes(page_string_in, 'utf-8'))
    page_string_out = page_bytes.decode('utf-8')

    url = 'http://127.0.0.1:80/'
    data = {
        'contents': page_string_out
    }
    headers = {
        'Content-Type': 'application/json', 
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)

    content = ContentFile(response.content)

    file_name = "{0}_{1}.pdf".format(check.order["id"], check.ctype)
    check.pdf_file.save(file_name, content, save=True)

    check.status = 'rendered'
    check.save() 