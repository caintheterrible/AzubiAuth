import os
from pathlib import Path
from typing import List
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class BaseConfiguration:
    """Core Django configuration preferences."""
    def __init__(self):
        self._secret_key=os.environ.get('DJANGO_SECRET_KEY')
        self.base_dir=Path(__file__).resolve().parent.parent.parent
        self._root_urlconf='config.urls'
        self._allowed_hosts_conf:list=['127.0.0.1', 'localhost']

        self._validate_environ()

    @staticmethod
    def _validate_environ()->None:
        """Validates required environment variables if existent."""
        required:list=['DJANGO_SECRET_KEY']
        missing_env_var:list=[var for var in required if not os.environ.get(var)]
        if missing_env_var:
            raise ValueError(f"Missing required environment variable: '{' '.join(missing_env_var)}' variable.")

    @property
    def secret_key(self)->str:
        """Secret key getter."""
        if not self._secret_key:
            raise ValueError(f"'DJANGO_SECRET_KEY' environment variable expected, but not required.")
        return self._secret_key

    @property
    def installed_apps(self)->List[str]:
        """List of installed third party and project-specific built applications."""
        third_party:list=[]
        project_apps:list=[]
        if not third_party and project_apps:
            print("'INSTALLED_APPS' list is empty.")
        return third_party+project_apps

    @property
    def middleware(self)->List[str]:
        """List of deployed middleware. CAUTION: Order of arrangement is critical."""
        default:list=[
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
        ]
        custom:list=[]
        return default+custom

    @property
    def root_url_configurations(self)->str:
        """URL path configurations."""
        return self._root_urlconf

    @property
    def allowed_hosts(self)->List[str]:
        """Fetches list of allowed hosts."""
        return self._allowed_hosts_conf


@lru_cache(maxsize=1)
def base_config()->BaseConfiguration:
    """Cached instance of BaseConfiguration."""
    return BaseConfiguration()

configurations:BaseConfiguration=base_config()