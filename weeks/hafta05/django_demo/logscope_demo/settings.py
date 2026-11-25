"""Isolated Django traffic simulator: local-only, no production credentials or real users."""
import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.environ.get('LOGSCOPE_DJANGO_SECRET','dev-only-not-for-public-deployment')
DEBUG=True
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.sessions','django.contrib.staticfiles','events']
MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'events.middleware.SafeAccessLogMiddleware'
]
ROOT_URLCONF='logscope_demo.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates',
  'DIRS':[BASE_DIR/'templates'], 'APP_DIRS':True,
  'OPTIONS':{'context_processors':['django.template.context_processors.request']}}]
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'django_demo.sqlite3'}}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
USE_TZ=True
TIME_ZONE='UTC'
STATIC_URL='/static/'
STATICFILES_DIRS=[BASE_DIR/'static']
LOGSCOPE_JSONL_PATH=os.environ.get('LOGSCOPE_JSONL_PATH',str(BASE_DIR/'generated_access.jsonl'))
LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS=os.environ.get('LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS','0')=='1'
