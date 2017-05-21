#!/bin/bash
# mkdeb.sh: create a .deb package
# Requires: python3-setuptools python3-stdeb

python3 setup.py --command-packages=stdeb.command bdist_deb
