from django.http import JsonResponse, HttpResponse
from django.views import View
import json

from apps.authentication_module.database_interface import DatabaseInterface
from apps.authentication_module.parser import RequestParser
from apps.authentication_module.security import SecurityHandler
from apps.authentication_module.validation_engine import ValidationEngine


class RegistrationView(View):
    """Class-based view with manual method dispatch."""
    def __init__(self):
        super().__init__()
        self.allowed_methods=['POST', 'OPTIONS']
        self.request_parser=RequestParser()
        self.validator=ValidationEngine()
        self.security_handler=SecurityHandler()
        self.db_interface=DatabaseInterface()

    def dispatch(self, request, *args, **kwargs):
        """Manual method dispatch with security checks."""
        # Method validation
        if request.method not in self.allowed_methods:
            return self.method_not_allowed(request)

        # Security middleware chain
        security_response=self.security_handler.process_request(request)
        if security_response:
            return security_response

        # Route to appropriate handler
        handler=getattr(self, request.method.lower(), None)
        if handler:
            return handler(request, *args, **kwargs)

        return self.method_not_allowed(request)

    def post(self, request, *args, **kwargs):
        """Registration endpoint handler."""
        try:
            # Parse request
            parsed_data=self.request_parser.parse(request)

            # Validate input
            validation_result=self.validator.validate_registration(parsed_data)
            if not validation_result.is_valid:
                return self.error_response(validation_result.errors, 400)

            # check user existence
            if self.db_interface.user_exists(parsed_data['email']):
                return self.error_response({
                    'email':'User already exists!'
                }, 409)

            # Create user
            user_id=self.db_interface.create_user(parsed_data)

            return self.success_response({
                'user_id':user_id,
                'message':'Registration successful!'
            }, 201)

        except Exception as exc:
            return self.error_response({
                'error':'Internal server error'
            }, 500)

    def options(self, request, *args, **kwargs):
        """CORS preflight handler."""
        response=HttpResponse()
        response['Access-Control-Allow-Origin']='*'
        response['Access-Control-Allow-Methods']='POST, OPTIONS'
        response['Access-Control-Allow-Headers']='Content-Type, X-CSRFToken'

        return response

    def method_not_allowed(self,request):
        return JsonResponse(data={
            'error':'Method not allowed!'
        }, status=405)

    def success_response(self, data, status=200):
        response=JsonResponse(data, status)
        self.add_security_headers(response)
        return response

    def error_response(self, data, status=400):
        response=JsonResponse(data, status)
        self.add_security_headers(response)
        return response

    def add_security_headers(self, response):
        response['X-Content-Type-Options']='nosniff'
        response['X-Frame-Options']='Deny'
        response['X-XSS-Protection']='1; mode=block'
        response['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
