"""Configuration module manager for application deployment. Works as DJANGO_SETTINGS_MODULE and loads configurations to `manage.py`."""

from pathlib import Path
from config.base import base_configurations
from config.development import development_configurations
from config.sqlconfig import get_sqlite_database_config

# Environment-specific configurations- to configure dynamic module loading
DEBUG:bool=development_configurations.debug     # to be set as environment-specific configuration
ALLOWED_HOSTS:list=development_configurations.allowed_hosts # this is to be set as an environment-specific configuration

# Base Django application configurations
SECRET_KEY:str=base_configurations.secret_key
BASE_DIR:Path=base_configurations.base_dir
ROOT_URLCONF:str=base_configurations.root_url_configurations

# Database configurations- to re-configure to accept dynamic loading of configurations
DATABASES={
    'default':get_sqlite_database_config('db.sqlite3'),
    'analytics':get_sqlite_database_config('analytics.sqlite3', max_connections=15)
}

# other settings
LANGUAGE:str='en-us'
USE_TZ:bool=True
USE_L10N:bool=True
USE_I10N:bool=True