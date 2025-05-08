import os

import bitcaster_sdk
print(os.getenv("BITCASTER_BAE"))
bitcaster_sdk.init()
from bitcaster_sdk import trigger

trigger(project='cbt', application='application', event='event1')