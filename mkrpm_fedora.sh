#!/bin/bash
# Build RPM for Fedora
# eg. ./mkrpm_fedora.sh fc16
dist=$1
[ -z "$dist" ] && echo "$0 {dist}" && exit 1
spectool -g -R sasutils.spec
rpmbuild --define "dist .$dist" -ba sasutils.spec
