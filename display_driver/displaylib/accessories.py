# Basic Python libraries
import datetime
import threading
import time
from typing import Dict

# Third-party libraries
import requests


# URL at which accessory state can be read, particularly for 'toggle_1' which
# determines whether output should be sent to the display
ACCESSORIES_URL = 'http://192.168.1.81/accessories'

# How often to poll the state of accessories
ACCESSORY_PERIOD = datetime.timedelta(seconds=5)

# Volatile indicator for whether accessories indicate that the display should be
# active
display_enabled = True


def poll_accessories() -> Dict:
  try:
    return requests.get(ACCESSORIES_URL).json()
  except requests.RequestException as e:
    print('Error polling accessories: {}'.format(e))
    return {}
  except ValueError as e:
    print('Error parsing accessories response: {}'.format(e))
    return {}


def accessory_loop():
  global display_enabled
  last_poll = datetime.datetime.utcnow()
  while True:
    while last_poll < datetime.datetime.utcnow():
      last_poll += ACCESSORY_PERIOD
    dt = (last_poll - datetime.datetime.utcnow()).total_seconds()
    if dt > 0:
      time.sleep(dt)
    accessories = poll_accessories()
    display_enabled = accessories.get('toggle_1', False)


def start_polling():
  threading.Thread(target=accessory_loop, daemon=True).start()
