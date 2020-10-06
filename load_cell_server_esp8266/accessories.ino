const int PIN_LED = 0; // "D3" on LoLin NodeMCU v3
const int PIN_SWITCH = 2; // "D4" on LoLin NodeMCU v3

void initAccessories() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_SWITCH, INPUT_PULLUP);
}

void ledOn() {
  digitalWrite(PIN_LED, 1);
}

void ledOff() {
  digitalWrite(PIN_LED, 0);
}

bool getSwitchState() {
  return digitalRead(PIN_SWITCH) == LOW;
}
