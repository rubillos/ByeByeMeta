#!/bin/bash

pip3 install --upgrade pip
pip3 install beautifulsoup4
pip3 install python-dateutil
pip3 install requests
pip3 install Pillow
pip3 install opencv-python

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    pip3 install windows-filedialogs
fi
