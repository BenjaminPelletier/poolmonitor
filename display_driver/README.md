# display_driver
## Overview
This folder contains a Python program that continuously queries the
[load cell server](../load_cell_server_esp8266) for the load cell (and
accessories) state and displays that information visually on the RGB matrix.

## Setting up a Raspberry Pi
* Write a non-GUI version of
[Raspberry Pi OS](https://www.raspberrypi.org/documentation/installation/installing-images/)
to a micro SD card, insert it in the Pi, and boot up
* Follow [Step 6 on the Adafruit guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices#step-6-log-into-your-pi-to-install-and-run-software-1745233-16):
  * `curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh >rgb-matrix.sh`
  * `sudo bash rgb-matrix.sh`
* Set up virtualenv
  * `sudo apt-get install python3-venv -y`
  * `python3 -m venv ../venv`
  * `source ../venv/bin/activate`
* Follow [binding build instructions](https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python):
  * `sudo apt-get update && sudo apt-get install python3-dev python3-pillow -y`
  * `make build-python PYTHON=$(which python3)`
  * `sudo make install-python PYTHON=$(which python3)`
* Install necessary packages
  * `sudo apt-get install libopenjp2-7`
  * `pip3 install image`
  * `pip3 install requests`
  * `pip3 install jsonschema`
  * `sudo apt-get install libatlas-base-dev`
  * `pip3 install numpy`
  * `pip3 install scikit-image`

## Startup
Assuming the Pi is not configured to run this program at startup, start the
display server in the background by:
* In
[RaspController](https://play.google.com/store/apps/details?id=it.Ettore.raspcontroller)
while connected to the router that the Pi is also connected to, select poolpi
(or appropriate), then select SSH Shell
* `cd ~/poolmonitor/display_driver` (or as appropriate)
* `sudo ./start_driver.py &`
  * The ampersand indicates to run the program in the background
* `logout`

## Stopping
To stop the display driver from running in the background after following the
steps in the previous section, follow the instructions again, but instead of
using the command `sudo ./start_driver.py &`, use the command
`sudo ./stop_driver.py` (note the lack of ampersand).

## Shutdown
The Raspberry Pi is a real computer and should be shut down gracefully to avoid
corruption.  To do this,
* In RaspController, select poolpi (or appropriate)
* Scroll near the bottom and select Shutdown Device
