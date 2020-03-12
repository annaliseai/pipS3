#!/bin/bash
# Build wheel

set -euo pipefail

export LANG=en_AU.utf8

/opt/python/cp37-cp37m/bin/python setup.py sdist

/opt/python/cp37-cp37m/bin/pip install dist/*.tar.gz

s3pkgup
