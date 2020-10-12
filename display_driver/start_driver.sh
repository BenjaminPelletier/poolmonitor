#!/bin/bash

source ../venv/bin/activate

export PYTHON_PATH=`pwd`/..
echo $PYTHON_PATH

which python3
echo $USER
python3 display_driver.py &
