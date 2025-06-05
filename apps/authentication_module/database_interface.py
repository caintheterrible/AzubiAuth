from django.db import connection, transaction
import secrets
import uuid
from datetime import datetime

from apps.authentication_module.errors import DatabaseError
from apps.authentication_module.security import PasswordHasher


class DatabaseInterface:
    """Raw SQL database operations."""
    def __init__(self):
        self.hasher=PasswordHasher()

    def user_exists(self, email):
        """Checks if user exists."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE email = %s"
                [email]
            )
            count=cursor.fetchone()[0]
            return count>0

    def create_user(self, user_data):
        """Creates user."""
        try:
            with transaction.atomic():
                user_id=self._insert_user(user_data)
                self._create_user_profile(user_id, user_data)
                return user_id
        except Exception as exc:
            raise DatabaseError(f"Failed to create user: {str(exc)}")

    def _insert_user(self, user_data):
        """Insert into auth_user table."""
        username=self._generate_username(user_data['email'])
        hashed_password=self.hasher.hash_password(user_data['password'])

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO auth_user (
                    username, email, first_name, last_name,
                    password, is_active, is_staff, is_superuser,
                    date_joined, last_login
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, [
                username,
                user_data['email'],
                user_data['first_name'],
                user_data['last_name'],
                hashed_password,
                True, # is_active
                False, # is_staff
                False, # is_superuser
                datetime.now(),
                None # last_login
            ])

            user_id=cursor.fetchone()[0]
            return user_id

    def _create_user_profile(self,user_id, user_data):
        """Create additional user profile data."""
        profile_id=str(uuid.uuid4())

        with connection.cursor() as cursor:
            # Create custom user profile table if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES auth_user(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email_verified BOOLEAN DEFAULT FALSE,
                    verification_token VARCHAR(255)
                )
            """)

            verification_token=secrets.token_urlsafe(32)
            cursor.execute("""
                INSERT INTO user_profiles (
                    id, user_id, email_verified, verification_token
                ) VALUES (%s, %s, %s, %s)
            """, [
                profile_id,
                user_id,
                False,
                verification_token
            ])

    def _generate_username(self, email):
        """Generates unique username from email."""
        base_username=email.split('@')[0]
        username=base_username

        counter=1
        while self._username_exists(username):
            username=f"{base_username}{counter}"
            counter+=1

        return username

    def _username_exists(self, username):
        """Checks if username exists."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM auth_user WHERE username = %s",
                [username]
            )
            return cursor.fetchone()[0]>0