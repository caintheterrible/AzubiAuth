import re

class ValidationResult:
    """Validation result container."""

    def __init__(self):
        self.is_valid=True
        self.errors={}

    def add_error(self, field, message):
        if field not in self.errors:
            self.errors[field]=[]
        self.errors[field].append(message)
        self.is_valid=False


class ValidationEngine:
    """Custom validation engine."""
    def validate_registration(self, data):
        result=ValidationResult()

        # Required fields
        required_fields=['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                result.add_error(field, message=f"{field} is required!")

        # Email validation
        if data.get('email'):
            if not self.is_valid_email(data['email']):
                result.add_error('email', message='Invalid email format!')

        # Password validation
        if data.get('password'):
            password_errors=self.validate_password(data['password'])
            for error in password_errors:
                result.add_error('password', error)

        # Name validation
        for name_field in ['first_name', 'last_name']:
            if data.get(name_field):
                if not self.is_valid_name(data[name_field]):
                    result.add_error(name_field, message='Name contains invalid characters')

        return result

    def is_valid_email(self, email):
        """Email regex validation."""
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """Password strength validation."""
        errors=[]
        if len(password)<8:
            errors.append('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?"{}|<>]', password):
            errors.append('Password must contain at least one special character')

        # Check for common passwords (update with a list instead)
        common_passwords:list=['password', '123456', 'qwerty', 'admin']
        if password.lower() in common_passwords:
            errors.append('Password is too common')

        return errors

    def is_valid_name(self, name):
        """Name validation - only letters, spaces, hyphens."""
        pattern:str=r'^[a-zA-Z\s\-\']+$'
        return re.match(pattern, name) is not None and len(name.strip())>8