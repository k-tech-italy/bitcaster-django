import os
import pathlib
import sys

import django


BASE_DIR = pathlib.Path(__file__).resolve()
PROJECT_ROOT = BASE_DIR.parents[1]
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(TESTS_DIR))


def pytest_configure(config):
    os.environ.update(DJANGO_SETTINGS_MODULE="demoapp.demo.settings")
    django.setup()
