import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt # Only for testing purposes. All routes in module in production environments are to be protected

@csrf_exempt
def register(request):
    if request.method!='POST':
        return HttpResponseBadRequest(
            f"REQUEST FAILED: Expected 'POST' request."
        )

    try:
        body_unicode=request.body.decode('utf-8')
        data= json.loads(body_unicode)
    except Exception as exc:
        return JsonResponse(
            {'error':'INVALID JSON'},status=400
        )

    username:str=data.get('username')
    email:str=data.get('email')
    password:str=data.get('password')

    if not username or not email or not password:
        return JsonResponse({
            'error':'Missing fields'
        }, status=400)

    # temporary simulated success
    return JsonResponse({
        'message':'User registered successfully!',
        'username':username,
        'email':email,
        'password':password,
    }, status=201)