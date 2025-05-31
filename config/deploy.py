from pathlib import Path
from config.base import base_configurations
from config.sqlconfig import get_sqlite_database_config

BASE_DIR:Path=base_configurations.base_dir
ALLOWED_HOSTS:list=base_configurations.allowed_hosts
ROOT_URLCONF:str=base_configurations.root_url_configurations
DATABASES={
    'default':get_sqlite_database_config('db.sqlite3'),
    'analytics':get_sqlite_database_config('analytics.sqlite3', max_connections=15)
}

print(DATABASES)