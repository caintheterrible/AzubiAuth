import urllib.parse
import json
from apps.authentication_module.security import InputSanitizer


class RequestParser:
    """Custom request parser."""
    def __init__(self):
        self.sanitizer=InputSanitizer()

    def parse(self, request):
        """Parses request data based on content type."""
        content_type=request.META.get('CONTENT_TYPE', '').lower()

        if 'application/json' in content_type:
            return self.parse_json(request)
        elif 'application/x-www-form-urlencoded' in content_type:
            return self.parse_form_data(request)
        elif 'multipart/form-data' in content_type:
            return self.parse_multipart(request)
        else:
            raise ValueError("Unsupported content type.")

    def parse_json(self, request):
        """Parses JSON request body."""
        try:
            raw_body=request.body.decode('utf-8')
            data=json.loads(raw_body)

            # Sanitize all string values
            return self.sanitize_dict(data)

        except (json.JSONDecodeError, UnicodeDecodeError) as decode_err:
            raise ValueError(f"Invalid JSON: {str(decode_err)}")

    def parse_form_data(self, request):
        """Parses URL-encoded form data."""
        try:
            raw_body=request.body.decode('utf-8')
            parsed=urllib.parse.parse_qs(raw_body)

            # Convert lists to single values and sanitize
            data={}
            for key, value_list in parsed.items():
                data[key]= value_list[0] if value_list else ''

            return self.sanitize_dict(data)

        except UnicodeDecodeError as decode_err:
            raise ValueError(f"Invalid form data: {str(decode_err)}")

    def parse_multipart(self, request):
        """Basic multipart parsing (files not supported in this)."""
        # Treating as form data for basic registration purposes
        return self.parse_form_data(request=request)

    def sanitize_dict(self, data):
        """Recursively sanitize dictionary values."""
        if isinstance(data, dict):
            return {
                key:self.sanitize_dict(value) for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                self.sanitize_dict(item) for item in data
            ]
        elif isinstance(data, str):
            return self.sanitizer.sanitize_html(data)
        else:
            return data