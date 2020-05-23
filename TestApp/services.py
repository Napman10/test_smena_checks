import json
import django_rq

def create_checks(order):
    #получаем заказ
    order = json.loads(order)
    #получаем принтеры на точке
    local_printers = Printer.objects.filter(point_id=order['point_id'])
    #получаем чеки принтеров
    checks = Check.objects.filter(printer_id__in=local_printers.values('pk'), order=order)
    #дополняем новыми чеками
    new_check_list = list()
    for p in local_printers:
        new_check = Check(printer_id=p, type=p.check_type, order=order)
        new_check_list.append(new_check)
    check_list = Check.objects.bulk_create(new_check_list)
    #добавляем в очередь чеки
    for c in check_list:
        django_rq.enqueue(#???)
        
def take_available_checks(api_key):
    #получаем принтеры по ключу
    printer_list = Printer.objects.filter(api_key=api_key)
    #получаем чеки
    ab_checks = Check.objects.filter(printer_id=printer_list.values('id'), status='rendered')
    return ab_checks
    
def take_pdf(api_key, check_id):
    #принтеры по ключу
    printer_list = Printer.objects.filter(api_key=api_key)
    #чек
    check = Check.objects.get(printer_id=printer_list.values('id'),pk=check_id)
    #доделать
    pdf = open(check.pdf_file.path, 'rb')
    
def pdf_worker(check_id):
    #получить чек
    check = Check.objects.get(pk=check_id)
    #обработать для двух разных случаев
    if check.type == "client":
        #инструкции
        pass
    if check.type == "kitchen":
        #инструкции
        pass
    #доделать обработку и сохранение
    
    