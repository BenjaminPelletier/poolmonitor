void handleRoot() {
  ledOn();
  String message =
    "<!DOCTYPE HTML>\n"
    "<html>\n"
    "<header>\n"
    "  <title>Load cell server</title>\n"
    "</header>\n"
    "<body>\n"
    "<a href=\"/loadcell\">Load cell</a><br>\n"
    "</body>\n"
    "</html>";
  server.send(200, "text/html", message);
  ledOff();
}

void handleAccessories() {
  ledOn();
  String message = "{\"toggle_1\": ";
  message += getSwitchState() ? "true" : "false";
  message += "}";
  server.send(200, "application/json", message);
  ledOff();
}

void handleLoadCell() {
  ledOn();
  String message =
    "<!DOCTYPE HTML>\n"
    "<html>\n"
    "<header>\n"
    "  <title>Load cell</title>\n"
    "</header>\n"
    "<body>\n"
    "<a href=\"/loadcell/status\">Status</a><br>\n"
    "<form method=\"post\" action=\"/loadcell/tare\">\n"
    "  <button type=\"submit\">Tare (zero) load cell</button>\n"
    "</form>\n"
    "<a href=\"/\">Home</a>\n"
    "</body>\n"
    "</html>";
  server.send(200, "text/html", message);
  ledOff();
}

void handleLoadCellTare() {
  ledOn();
  lcTare();
  String message =
    "<!DOCTYPE HTML>\n"
    "<html>\n"
    "<header>\n"
    "  <title>Load cell tare</title>\n"
    "</header>\n"
    "<body>\n"
    "Load cell successfully tared.<br>\n"
    "<a href=\"/loadcell\">Back to load cell information</a><br>\n"
    "<a href=\"/\">Home</a>\n"
    "</body>\n"
    "</html>";
  server.send(200, "text/html", message);
  ledOff();
}

void handleLoadCellStatus() {
  ledOn();
  String message =
    "{\n"
    "  \"sensor\": {\n"
    "    \"instantaneous_value\": ";
  message += lcGetLastInstantaneousSensorValue();
  message +=                      ",\n"
    "    \"integrated\": {\n"
    "      \"value\": ";
  message += lcGetLoadCellValue();
  message +=          ",\n"
    "      \"samples\": ";
  message += lcGetSamples();
  message +=            "\n"
    "    },\n"
    "    \"history\": {\n"
    "      \"time_index\": ";
  message += lcGetHistoryLength();
  message +=               ",\n"
    "      \"values\":\n"
    "        [";
  if (lcGetHistoryLength() > 0) {
    byte i = lcGetFirstHistoryIndex();
    bool first = true;
    while (true) {
      if (i >= lcGetSensorHistoryLength()) {
        i = 0;
      }
      if (i == lcGetLastHistoryIndex()) {
        break;
      }
      if (!first) {
        message += ", ";
      }
      first = false;
      message += lcGetValue(i);
      
      i++;
    }
  }
  message +=  "]\n"
    "    }\n"
    "  },\n"
    "  \"session\": {\n"
    "    \"mode\": \"";
  String sessionMode = lcGetSessionMode();
  message += sessionMode;
  message +=         "\",\n"
    "    \"duration\": ";
  message += lcGetSessionDuration();
  message +=               "\n"
    "  }\n"
    "}";
  server.sendHeader("Refresh", "1", false);
  server.send(200, "application/json", message);
  ledOff();
}

void handleNotFound() {
  ledOn();
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  server.send(404, "text/plain", message);
  ledOff();
}
