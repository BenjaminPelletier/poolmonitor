## Setting up a Raspberry Pi
* Follow [Step 6 on the Adafruit guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices#step-6-log-into-your-pi-to-install-and-run-software-1745233-16):
  * `curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh >rgb-matrix.sh`
  * `sudo bash rgb-matrix.sh`
* Set up virtualenv
  * `sudo apt-get install python3-venv -y`
  * `python3 -m venv ~/my_venv`
  * `source ~/my_venv/bin/activate`
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
