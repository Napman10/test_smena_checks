#from django.shortcuts import render #нет необходимости в этом стандартном импорте
from . import services
# Create your views here.
def create_checks(request):
    response = services.create_checks(request)
    return response

def new_checks(request):
    api_key = request.GET.get('api_key', '')
    response = services.new_checks(api_key)
    return response

def check(request):
    api_key = request.GET.get('api_key','')
    check_id = request.GET.get('check_id', '')
    response = services.take_pdf(api_key, check_id)
    return response