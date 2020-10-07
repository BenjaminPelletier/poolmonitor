#!/bin/bash

source ../venv/bin/activate

export PYTHON_PATH=`pwd`/..
echo $PYTHON_PATH

python3 display_driver.py
