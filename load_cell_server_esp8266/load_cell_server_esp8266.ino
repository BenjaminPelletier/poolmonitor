#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

const char* ssid = "PelletierBackyard";
const char* password = "sneakypants";

ESP8266WebServer server(80);

void setup(void) {
  initAccessories();
  ledOn();
  Serial.begin(115200);
  Serial.println("");
  
  Serial.println("Initializing...");
  lcInit();
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin("poolcell")) {
    Serial.println("MDNS responder started");
  }

  server.on("/", handleRoot);
  server.on("/loadcell", handleLoadCell);
  server.on("/loadcell/status", handleLoadCellStatus);
  server.on("/loadcell/tare", handleLoadCellTare);
  server.on("/accessories", handleAccessories);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started");

  lcFinishInit();
  ledOff();
  
  Serial.println("Ready to receive requests");
}

void loop(void) {
  // Add sensor measurement
  addSensorMeasurement(false);
  
  server.handleClient();
  MDNS.update();
}
