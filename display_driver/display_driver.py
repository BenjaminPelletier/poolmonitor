#!/usr/bin/env python

import datetime
import enum
import sys
import threading
import time
from typing import Dict, List, Optional

# Requires rgbmatrix installed via special procedure; see README.md
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

import jsonschema
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests


POLLING_PERIOD = datetime.timedelta(seconds=1)
POLLING_THREADS = 2

ACCESSORY_PERIOD = datetime.timedelta(seconds=5)


class LoadCellPoll(dict):
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
  Unknown = 0
  Waiting = 1
  Polling = 2
  Processing = 3


class Coordinator(object):
  def __init__(self, polling_threads: int):
    self._lock = threading.Lock()
    self.run_poll = True
    self._phase = [PollPhase.Waiting] * polling_threads
    self._loadcell: Optional[LoadCellPoll] = None
    self.display_enabled = False

  def get_phase(self, index: int) -> PollPhase:
    with self._lock:
      return self._phase[index]

  def set_phase(self, index: int, phase: PollPhase):
    with self._lock:
      self._phase[index] = phase

  def get_loadcell(self) -> Optional[LoadCellPoll]:
    with self._lock:
      return self._loadcell

  def update_loadcell(self, value: Optional[LoadCellPoll]):
    with self._lock:
      self._loadcell = value


coordinator = Coordinator(POLLING_THREADS)


def make_matrix() -> RGBMatrix:
  options = RGBMatrixOptions()

  options.rows = 32
  options.cols = 64
  options.chain_length = 1
  options.parallel = 1
  options.row_address_type = 0
  options.multiplexing = 0
  options.pwm_bits = 11
  options.brightness = 100
  options.pwm_lsb_nanoseconds = 130
  options.led_rgb_sequence = 'RGB'
  options.pixel_mapper_config = ''
  options.gpio_slowdown = 1

  return RGBMatrix(options=options)


def poll_accessories() -> Dict:
  try:
    return requests.get('http://192.168.1.81/accessories').json()
  except requests.RequestException as e:
    print('Error polling accessories: {}'.format(e))
    return {}
  except ValueError as e:
    print('Error parsing accessories response: {}'.format(e))
    return {}


def accessory_loop():
  global coordinator
  last_poll = datetime.datetime.utcnow()
  while coordinator.run_poll:
    while last_poll < datetime.datetime.utcnow():
      last_poll += ACCESSORY_PERIOD
    dt = (last_poll - datetime.datetime.utcnow()).total_seconds()
    if dt > 0:
      time.sleep(dt)
    accessories = poll_accessories()
    coordinator.display_enabled = accessories.get('toggle_1', False)


def poll_load_cell() -> Optional[LoadCellPoll]:
  try:
    response = LoadCellPoll(requests.get('http://192.168.1.81/loadcell/status').json())
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
    if coordinator.display_enabled:
      coordinator.set_phase(index, PollPhase.Polling)
      new_value = poll_load_cell()
      coordinator.set_phase(index, PollPhase.Processing)
      coordinator.update_loadcell(new_value)


def display_loop():
  global coordinator
  matrix = make_matrix()
  canvas = matrix.CreateFrameCanvas()
  font = graphics.Font()
  font.LoadFont("./fonts/7x13.bdf")
  img = np.zeros([100, 200, 3], dtype=np.uint8)

  red = graphics.Color(255, 0, 0)
  orange = graphics.Color(255, 128, 0)
  yellow = graphics.Color(255, 255, 0)
  darkgreen = graphics.Color(0, 32, 0)
  green = graphics.Color(0, 255, 0)
  blue = graphics.Color(0, 0, 255)

  turbo = plt.get_cmap('turbo')

  poll_colors = {
    PollPhase.Waiting: darkgreen,
    PollPhase.Polling: yellow,
    PollPhase.Processing: red,
    PollPhase.Unknown: blue,
  }

  session_colors = {
    'IDLE': red,
    'STARTING': yellow,
    'ACTIVE': green,
    'STOPPING': orange,
  }

  while True:
    canvas.Clear()

    if coordinator.display_enabled:
      loadcell = coordinator.get_loadcell()
      if loadcell is None:
        force_text = 'LC error'
        force_value = 0
        session_text = 'LC err'
        session_color = red
      else:
        force_text = '{:.1f} lb'.format(loadcell['sensor']['instantaneous_value'])
        force_value = loadcell['sensor']['instantaneous_value'] / 35
        session_text = str(datetime.timedelta(
          seconds=round(loadcell['session']['duration'])))
        session_color = session_colors[loadcell['session']['mode']]
      force_color_rgba = turbo(force_value)
      force_color = graphics.Color(round(force_color_rgba[0] * 255),
                                   round(force_color_rgba[1] * 255),
                                   round(force_color_rgba[2] * 255))

      graphics.DrawText(canvas, font, 0, 10, force_color, force_text)
      graphics.DrawText(canvas, font, 0, 20, session_color, session_text)
      for p in range(POLLING_THREADS):
        graphics.DrawCircle(canvas, 61, 2 + p * 5, 2,
                            poll_colors[coordinator.get_phase(p)])

    canvas = matrix.SwapOnVSync(canvas)
    time.sleep(0.05)


# Entry point
if __name__ == "__main__":
  try:
    # Start loop
    print("Press CTRL-C to stop")

    t0 = datetime.datetime.utcnow()
    poll_threads = [threading.Thread(target=poll_loop, args=(i, t0), daemon=True) for i in range(POLLING_THREADS)]
    for t in poll_threads:
      t.start()

    threading.Thread(target=accessory_loop, daemon=True).start()

    display_loop()
  except KeyboardInterrupt:
    print("Exiting\n")
    coordinator.run_poll = False
    sys.exit(0)
