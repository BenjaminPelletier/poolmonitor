#include <HX711.h>

const unsigned long UL_MAX = 0xFFFFFFFF;

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 5; // "D1" on LoLin NodeMCU v3
const int LOADCELL_SCK_PIN = 4; // "D2" on LoLin NodeMCU v3

// Load cell calibration
const float LOADCELL_SCALE = -6.536e4f; // ADC counts per pound

HX711 scale;

// Declare a global variable to keep track of the current integrated sensor reading
struct SensorIntegration {
  unsigned long startedAt;
  unsigned long lastMeasurement;
  float sum;
  float nSamples;
};
volatile float last_instantaneous_sensor_value = 0.0f;
SensorIntegration loadCellState;

// Declare a global variable to keep track of sensor history
volatile unsigned long history_length = 0;
const int MILLIS_PER_HISTORY_ENTRY = 1000;
const byte SENSOR_HISTORY_LENGTH = 60;
struct SensorHistory {
  float values[SENSOR_HISTORY_LENGTH];
  byte index;
  bool full;
};
SensorHistory loadCellHistory;

// Declare a global variable to keep track of session time
struct TimedSession {
  byte mode;
  unsigned long startedAt;
  byte steps;
};
TimedSession session;
const byte SESSIONMODE_IDLE = 0;
const byte SESSIONMODE_ACTIVE = 1;
const float SESSION_STARTFORCE = 3.0f; //lbf
const byte SESSION_STARTLENGTH = 5; //history entries
const float SESSION_STOPFORCE = 1.0f; //lbf
const byte SESSION_STOPLENGTH = 10; //history entries

unsigned long subtract(unsigned long a, unsigned long b) {
  if (a >= b) {
    return a - b;
  }
  return UL_MAX - a + 1 + b;
}

// ===== Accessors =====

float lcGetLastInstantaneousSensorValue() {
  return last_instantaneous_sensor_value;
}

float lcGetLoadCellValue() {
  return loadCellState.sum / loadCellState.nSamples;
}

float lcGetSamples() {
  return loadCellState.nSamples;
}

unsigned long lcGetHistoryLength() {
  return history_length;
}

byte lcGetFirstHistoryIndex() {
  return loadCellHistory.full ? loadCellHistory.index + 1 : 0;
}

byte lcGetSensorHistoryLength() {
  return SENSOR_HISTORY_LENGTH;
}

byte lcGetLastHistoryIndex() {
  return loadCellHistory.index;
}

float lcGetValue(byte i) {
  if (isnan(loadCellHistory.values[i])) {
    return -1;
  } else {
    return loadCellHistory.values[i];
  }
}

String lcGetSessionMode() {
  switch (session.mode) {
    case SESSIONMODE_IDLE:
      if (session.steps == 0) {
        return "IDLE";
      } else {
        return "STARTING";
      }
      break;
    case SESSIONMODE_ACTIVE:
      if (session.steps == 0) {
        return "ACTIVE";
      } else {
        return "STOPPING";
      }
      break;
  }
  return "UNKNOWN";
}

float lcGetSessionDuration() {
  if (session.mode == SESSIONMODE_ACTIVE) {
    return subtract(millis(), session.startedAt) / 1000.0f;
  } else {
    return 0;
  }
}

void lcTare() {
  scale.tare();
}

// ===== End of accessors =====

void lcInit() {
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(LOADCELL_SCALE);
}

void lcFinishInit() {
  // Tare the load cell
  Serial.println("Taring load cell...");
  scale.tare();

  session.mode = SESSIONMODE_IDLE;
  session.steps = 0;
  Serial.println("Adding initial sensor measurement...");
  addSensorMeasurement(true);

  Serial.println("Load cell initialization complete.");
}

void addSensorMeasurement(bool firstMeasurement) {
  // Read the instantaneous load cell tension
  float lbf = scale.get_units(1);
  last_instantaneous_sensor_value = lbf;
  unsigned long t = millis();

  // If this is the first measurement of all time, initialize state
  if (firstMeasurement) {
    loadCellState.startedAt = t;
    loadCellState.lastMeasurement = t;
    loadCellState.sum = lbf;
    loadCellState.nSamples = 1.0f;
    return;
  }
  
  // Update sensor integration state
  unsigned long t1 = loadCellState.startedAt + MILLIS_PER_HISTORY_ENTRY;
  if ((t1 > loadCellState.startedAt && t < t1) ||
      (t1 < loadCellState.startedAt && ((t < t1) || (t > loadCellState.startedAt)))) {
    // We haven't reached the end of the MILLIS_PER_HISTORY_ENTRY integration period
    loadCellState.lastMeasurement = t;
    loadCellState.sum += lbf;
    loadCellState.nSamples += 1.0f;
    return;
  }

  // We have reached the end of a MILLIS_PER_HISTORY_ENTRY integration period
  // Determine what fraction f of this measurement belongs to the current integration
  unsigned long dtSample;
  unsigned long dtEndOfIntegration;
  if (t > loadCellState.lastMeasurement) {
    dtSample = t - loadCellState.lastMeasurement;
  } else {
    dtSample = (UL_MAX - loadCellState.lastMeasurement) + t + 1;
  }
  if (t1 > loadCellState.lastMeasurement) {
    dtEndOfIntegration = t1 - loadCellState.lastMeasurement;
  } else {
    dtEndOfIntegration = (UL_MAX - loadCellState.lastMeasurement) + t1 + 1;
  }
  float f = (float)dtEndOfIntegration / dtSample;

  // Update sensor history
  float avg = (loadCellState.sum + lbf * f) / (loadCellState.nSamples + f);
  loadCellHistory.values[loadCellHistory.index] = avg;
  loadCellHistory.index++;
  history_length++;
  if (loadCellHistory.index >= SENSOR_HISTORY_LENGTH) {
    loadCellHistory.index = 0;
    loadCellHistory.full = true;
  }

  // Update session state
  switch (session.mode) {
    case SESSIONMODE_IDLE:
      if (avg >= SESSION_STARTFORCE) {
        session.steps++;
        if (session.steps >= SESSION_STARTLENGTH) {
          session.startedAt = t - MILLIS_PER_HISTORY_ENTRY * SESSION_STARTLENGTH;
          session.mode = SESSIONMODE_ACTIVE;
          session.steps = 0;
        }
      } else {
        session.steps = 0;
      }
      break;
    case SESSIONMODE_ACTIVE:
      if (avg < SESSION_STOPFORCE) {
        session.steps++;
        if (session.steps >= SESSION_STOPLENGTH) {
          session.mode = SESSIONMODE_IDLE;
          session.steps = 0;
        }
      } else {
        session.steps = 0;
      }
      break;
  }

  // Update load cell integration state
  loadCellState.startedAt += MILLIS_PER_HISTORY_ENTRY;
  loadCellState.lastMeasurement = t;
  loadCellState.sum = lbf * (1.0f - f);
  loadCellState.nSamples = 1.0f - f;
}
