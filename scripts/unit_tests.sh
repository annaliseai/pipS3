#!/bin/bash
# Run unittests

set -eo

export LANG=en_AU.utf8

/opt/python/cp37-cp37m/bin/pip install -r requirements.txt
/opt/python/cp37-cp37m/bin/pip install pytest

# Confirm the dictionaries
/opt/python/cp37-cp37m/bin/python utils/generate_dicom_dict.py
/opt/python/cp37-cp37m/bin/python utils/confirm_dicom_currency.py