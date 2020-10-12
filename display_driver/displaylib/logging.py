import datetime
import os
from typing import Dict, List, Optional, Tuple


class Logger(object):
  def __init__(self):
    os.makedirs('logs', exist_ok=True)
    self.history: Dict[int, float] = {}
    self.instantaneous: List[Tuple[float, float, float]] = []
    self.start_time_index: Optional[int] = None
    self.start_timestamp: Optional[datetime.datetime] = None
    self.session_valid = False

  def update(self, loadcell: Dict, initiated_at: datetime.datetime):
    t = datetime.datetime.utcnow()
    session = loadcell['session']
    if session['mode'] != 'IDLE':
      if session['mode'] == 'ACTIVE':
        self.session_valid = True
      sensor_history = loadcell['sensor']['history']
      if self.start_time_index is None:
        # A new session just started
        self.start_timestamp = initiated_at
        self.start_time_index = sensor_history['time_index'] + len(sensor_history['values']) - 1 - round(session['duration'])
      dt0 = sensor_history['time_index'] - self.start_time_index
      for i, v in enumerate(sensor_history['values']):
        if dt0 + i >= -15:
          self.history[dt0 + i] = v
      self.instantaneous.append((
        (initiated_at - self.start_timestamp).total_seconds(),
        (t - self.start_timestamp).total_seconds(),
        loadcell['sensor']['instantaneous_value']))

    elif self.start_time_index is not None and session['mode'] == 'IDLE':
      # A session just ended
      if self.session_valid:
        logname = os.path.abspath('logs/{}.csv'.format(self.start_timestamp.strftime('%Y-%m-%d_%H%M%S')))
        with open(logname, 'w') as f:
          f.write('History,,,Instantaneous\n')
          f.write('Seconds since session start,Tension (pounds),,Request initiated (Seconds since session start),Request completed (Seconds since session start),Tension (pounds)\n')
          history_list = [(k, self.history[k]) for k in sorted(self.history)]
          for i in range(max(len(history_list), len(self.instantaneous))):
            line = '{},{},,'.format(*history_list[i]) if i < len(history_list) else ',,,'
            line += '{},{},{}\n'.format(*self.instantaneous[i]) if i < len(self.instantaneous) else ',,,\n'
            f.write(line)
      self.history = {}
      self.instantaneous = []
      self.start_time_index = None
      self.start_timestamp = None
      self.session_valid = False
