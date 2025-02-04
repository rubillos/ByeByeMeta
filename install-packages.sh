#!/bin/bash

pip3 install --upgrade pip
pip3 install $1 beautifulsoup4
pip3 install $1 lxml
pip3 install $1 python-dateutil
pip3 install $1 requests
pip3 install $1 Pillow
pip3 install $1 opencv-python
pip3 install $1 rich

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    pip3 install $1 windows-filedialogs
fi
