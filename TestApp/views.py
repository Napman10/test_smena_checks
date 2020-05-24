from django.shortcuts import render
import services
# Create your views here.
def create_checks(request):
    response = services.create_checks(request)
    return response

def take_available_checks(request):
    api_key = request.GET.get('api_key', '')
    response = services.take_available_checks(api_key)
    return response

def take_pdf(request):
    check_id = request.GET.get('check_id', '')
    response = services.take_pdf(api_key, check_id)
    return response