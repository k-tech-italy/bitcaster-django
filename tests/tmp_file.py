import os
import sys
import pathlib
import django
import requests

BASE_DIR = pathlib.Path(__file__).resolve()
PROJECT_ROOT = BASE_DIR.parents[1]
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(TESTS_DIR))

os.environ.update(DJANGO_SETTINGS_MODULE="demoapp.demo.settings")
django.setup()

from bitcaster_django.client import Client

# from bitcaster_django.client import Client
client = Client()
response = client.post('/u/', data={'email': 'user32@example.com'})
# response = requests.get('http://localhost:8000/api/system/ping', headers={
#     'Authorization': 'Key 2Uu1PMyOEGHrgEhv7fJW~OLEA-1gVMd0mfi2Ap8IkuEMnEYeXFGXqgFhYEmey6vb5Sg-LhHofsiiidvt37H2S34eE5_qfbT3'
# })
# breakpoint()