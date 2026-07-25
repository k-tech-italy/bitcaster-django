import os
import sys
from pathlib import Path

here = Path(__file__).parent
sys.path.insert(0, str(here / "../src"))
sys.path.insert(0, str(here / "demoapp"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")
