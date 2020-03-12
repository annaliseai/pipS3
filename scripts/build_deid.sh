#!/bin/bash
# Build wheel 

set -eo

export LANG=en_AU.utf8

# Install zip for artifacts
yum install -y zip

/opt/python/cp37-cp37m/bin/pip install -r requirements.txt
/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel