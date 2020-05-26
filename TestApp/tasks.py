from django_rq import job  
from .models import Check
from django.template.loader import render_to_string
import base64
import requests
import json
from django.core.files.base import ContentFile

def wkhtmltopdf(check_id):
    print("Here")
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