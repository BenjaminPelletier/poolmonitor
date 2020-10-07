# Basic Python libraries
import datetime
import enum
import threading
import time
from typing import Dict, Optional

# Third-party libraries
import jsonschema
import requests

# Libraries in this project
from . import accessories


# URL at which load cell information can be retrieved
# See LoadCellPoll for expected schema
LOADCELL_STATUS_URL = 'http://192.168.1.81/loadcell/status'

POLLING_PERIOD = datetime.timedelta(seconds=1)
POLLING_THREADS = 2

class LoadCellPoll(dict):
  """Convenience class wrapping a dict that ensures validity of data."""
  SCHEMA = {
    'type': 'object',
    'properties': {
      'sensor': {
        'type': 'object',
        'properties': {
          'instantaneous_value': {'type': 'number'},
          'integrated': {
            'type': 'object',
            'properties': {
              'value': {'type': 'number'},
              'samples': {'type': 'number'},
            },
            'required': ['value', 'samples'],
          },
          'history': {
            'type': 'object',
            'properties': {
              'time_index': {'type': 'number'},
              'values': {
                'type': 'array',
                'items': {'type': 'number'},
              }
            },
            'required': ['time_index', 'values'],
          },
        },
        'required': ['instantaneous_value', 'integrated', 'history'],
      },
      'session': {
        'type': 'object',
        'properties': {
          'mode': {
            'type': 'string',
            'enum': ['IDLE', 'STARTING', 'ACTIVE', 'STOPPING'],
          },
          'duration': {'type': 'number'},
        },
        'required': ['mode', 'duration'],
      },
    },
    'required': ['sensor', 'session'],
  }

  def __init__(self, data: Dict):
    super(LoadCellPoll, self).__init__(data)
    jsonschema.validate(instance=self, schema=LoadCellPoll.SCHEMA)


class PollPhase(enum.Enum):
  """The current state of a thread polling the load cell server."""
  Unknown = 0
  Waiting = 1 # Sleeping until the next scheduled poll
  Polling = 2 # Active network request
  Processing = 3 # Processing response locally


class Coordinator(object):
  """
  Coordinator between multiple load cell polling threads that provides a single
  unified current load cell status.  Also tracks the states of each polling
  thread.
  """
  def __init__(self, polling_threads: int):
    self._lock = threading.Lock()
    self.run_poll = True
    self._phase = [PollPhase.Waiting] * polling_threads
    self._loadcell_timestamp = datetime.datetime.utcnow()
    self._loadcell: Optional[LoadCellPoll] = None
    self._loadcell_errors: int = 0

  def get_phase(self, index: int) -> PollPhase:
    with self._lock:
      return self._phase[index]

  def set_phase(self, index: int, phase: PollPhase):
    with self._lock:
      self._phase[index] = phase

  def get_loadcell(self) -> Optional[LoadCellPoll]:
    with self._lock:
      return self._loadcell

  def update_loadcell(self,
                      initiated_at: datetime.datetime,
                      value: Optional[LoadCellPoll]):
    with self._lock:
      if initiated_at > self._loadcell_timestamp:
        if value is not None:
          self._loadcell_timestamp = initiated_at
          self._loadcell = value
          self._loadcell_errors = 0
        else:
          self._loadcell_errors += 1
          if self._loadcell_errors >= 5:
            self._loadcell = None


coordinator = Coordinator(POLLING_THREADS)


def poll_load_cell() -> Optional[LoadCellPoll]:
  try:
    response = LoadCellPoll(requests.get(LOADCELL_STATUS_URL).json())
  except requests.RequestException as e:
    print('Error polling load cell: {}'.format(e))
    return None
  except ValueError as e:
    print('Error parsing load cell response: {}'.format(e))
    return None
  except jsonschema.ValidationError as e:
    print('Load cell response was invalid: {}'.format(e))
    return None

  return response


def poll_loop(index: int, t0: datetime.datetime):
  global coordinator
  last_poll = t0 + datetime.timedelta(seconds=index * POLLING_PERIOD.total_seconds() / POLLING_THREADS)
  while coordinator.run_poll:
    while last_poll < datetime.datetime.utcnow():
      last_poll += POLLING_PERIOD
    dt = (last_poll - datetime.datetime.utcnow()).total_seconds()
    if dt > 0:
      coordinator.set_phase(index, PollPhase.Waiting)
      time.sleep(dt)
    if accessories.display_enabled:
      coordinator.set_phase(index, PollPhase.Polling)
      t0 = datetime.datetime.utcnow()
      new_value = poll_load_cell()
      coordinator.set_phase(index, PollPhase.Processing)
      coordinator.update_loadcell(t0, new_value)


def start_polling():
  t0 = datetime.datetime.utcnow()
  poll_threads = [threading.Thread(target=poll_loop, args=(i, t0), daemon=True)
                  for i in range(POLLING_THREADS)]
  for t in poll_threads:
    t.start()
