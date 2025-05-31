from pathlib import Path
from config.base import base_configurations
from config.database import db_configurations
# import config.env

BASE_DIR:Path=base_configurations.base_dir
ALLOWED_HOSTS:list=base_configurations.allowed_hosts
ROOT_URLCONF:str=base_configurations.root_url_configurations

DATABASES={
    'default':{
        'ENGINE':'django.db.backends.sqlite3',
        'NAME': BASE_DIR/'db.sqlite3',
    }
}