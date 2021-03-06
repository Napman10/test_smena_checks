from . import services
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
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
    response = services.check(api_key, check_id)
    return response