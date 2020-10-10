# ESP8266 load cell server

## Overview
This Arduino sketch continously reads the load cell, pausing only to serve web
requests from a webserver it is hosting.

## Electrical connections
This sketch assumes (see [accessories](accessories.ino)) that there is an LED
connected to D3 and a switch connected to D4.  Note that the ESP8266 runs on
3.3V, so you will need to level-convert if you want to use the 5V USB power.

The HX711 should be powered by 5V, DOUT should be connected to D1, and SCK to D2
(see [load_cell](load_cell.ino) for confirmation).

## Setup
After downloading and installing the
[Arduino IDE](https://www.arduino.cc/en/Main/software), you must add the board
information for the ESP8266 following
[this guide](https://www.instructables.com/Getting-Started-With-ESP8266LiLon-NodeMCU-V3Flashi/).
Open [load_cell_server_esp8266.ino](load_cell_server_esp8266.ino) in the IDE.
