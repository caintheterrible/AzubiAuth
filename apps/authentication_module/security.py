import hashlib
import secrets
import hmac
import time
from django.core.cache import cache
from django.http import JsonResponse


class SecurityHandler:
    """Custom security middleware with CSRF and rate limiting features."""
    def __init__(self):
        self.csrf_secret=secrets.token_urlsafe(32)

    def process_request(self, request):
        """Process security checks."""
        # Rate limiting
        rate_limit_response=self.check_rate_limit(request)
        if rate_limit_response:
            return rate_limit_response

        # CSRF validation (except for OPTIONS)
        if request.method!='OPTIONS':
            csrf_response=self.validate_csrf(request)
            if csrf_response:
                return csrf_response

        return None

    def check_rate_limit(self, request):
        """Checks request rate limit implementations."""
        client_ip=self.get_client_ip(request)
        cache_key=f"rate_limit: {client_ip}"

        current_requests=cache.get(cache_key, 0)
        if current_requests>=10: # 10 requests per minute
            return JsonResponse(data={
                'error':'Rate limit exceeded',
            }, status=429)

        cache.set(cache_key, current_requests + 1, 60)
        return None

    def validate_csrf(self, request):
        """CSRF token validation."""
        token=request.headers.get('X-CSRFToken') or request.POST.get('csrfmiddlewaretoken')

        if not token:
            return JsonResponse(data={
                'error':'CSRF token missing'
            }, status=403)

        if not self.is_valid_csrf_token(token):
            return JsonResponse(data={
                'error':'CSRF token invalid'
            }, status=403)

        return None

    def generate_csrf_token(self):
        """Generates CSRF token."""
        timestamp=str(int(time.time()))
        message=f"{timestamp}:{secrets.token_urlsafe(32)}"
        signature=hmac.new(
            self.csrf_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{message}:{signature}"

    def is_valid_csrf_token(self, token):
        """Validates CSRF token."""
        try:
            parts=token.split(':')
            if len(parts)!=3:
                return False

            timestamp, random_part, signature= parts
            message=f"{timestamp}:{random_part}"

            expected_signature=hmac.new(
                self.csrf_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            # Constant time comparison
            if not hmac.compare_digest(signature, expected_signature):
                return False

            # Check timestamp (24 hour expiry)
            if int(time.time())-int(timestamp)>86400:
                return False

            return True

        except(ValueError, TypeError):
            return False

    def get_client_ip(self, request):
        """Extracts client IP address with proxy support."""
        x_forwarded_for=request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class PasswordHasher:
    """Password hashing functionality."""
    @staticmethod
    def hash_password(password, salt=None):
        """Hashes password using PBKDF2 with SHA256."""
        if salt is None:
            salt=secrets.token_bytes(32)
        elif isinstance(salt, str):
            salt=salt.encode('utf-8')

        # PBKDF2 iterations
        hashed= hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

        return salt.hex()+':'+hashed.hex()

    @staticmethod
    def verify_password(password, hashed_password):
        """Verifies password against hash."""
        try:
            salt_hex, hash_hex= hashed_password.split(':')
            salt=bytes.fromhex(salt_hex)
            stored_hash=bytes.fromhex(hash_hex)

            # Hash provided password with stored salt
            computed_hash=hashlib.pbkdf2_hmac(
                'sha256', password.encode('utf-8'), salt, 100000
            )

            # Constant time comparison
            return hmac.compare_digest(stored_hash, computed_hash)
        except(ValueError, TypeError):
            return False


class InputSanitizer:
    """Input sanitization functionalities."""
    @staticmethod
    def sanitize_html(text):
        """Remove HTML tags and dangerous characters."""
        if not isinstance(text, str):
            return str(text)

        # Remove HTML tags
        import re
        clean=re.compile('<.*?>')
        text=re.sub(clean, '', text)

        # Escape dangerous characters
        replacements={
            '<':'&lt;',
            '>':'&gt;',
            '"':'&quot;',
            "'":'&#x27;',
            '&':'&amp;',
        }

        for char, escape in replacements.items():
            text=text.replace(char, escape)

        return text.strip()

    @staticmethod
    def sanitize_sql(text):
        """Basic SQL injection prevention."""
        if not isinstance(text, str):
            return str(text)

        dangerous_patterns:list=[
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|#|\|\*|\*\/)',
            r'(\bOR\b.*=.*)',
            r'(\bAND\b.*=.*)',
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("Potentially dangerous input detected!")

        return text