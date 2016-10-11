#
# Copyright (C) 2016
#      The Board of Trustees of the Leland Stanford Junior University
# Written by Stephane Thiell <sthiell@stanford.edu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SES utilities

Requires sg_ses from sg3_utils (recent version, like 1.77).
"""

__author__ = 'sthiell@stanford.edu (Stephane Thiell)'

import logging
import re
import subprocess


LOGGER = logging.getLogger(__name__)


def ses_get_snic_nickname(sg_devname):
    """Get subenclosure nickname (SES-2) [snic]"""
    # SES nickname is not available through sysfs, use sg_ses tool instead
    cmdargs = ['sg_ses', '--page=snic', '-I0', '/dev/' + sg_devname]
    LOGGER.debug('ses_get_snic_nickname: executing: %s', cmdargs)
    stdout, stderr = subprocess.Popen(cmdargs,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()

    for line in stderr.splitlines():
        LOGGER.debug('ses_get_snic_nickname: sg_ses(stderr): %s', line)

    for line in stdout.splitlines():
        LOGGER.debug('ses_get_snic_nickname: sg_ses: %s', line)
        mobj = re.match(r'\s+nickname:\s*([^ ]+)', line)
        if mobj:
            return mobj.group(1)

def _ses_get_ed_line(sg_devname):
    """Helper function to get element descriptor associated lines."""
    cmdargs = ['sg_ses', '--page=ed', '--join', '/dev/' + sg_devname]
    LOGGER.debug('ses_get_ed_metrics: executing: %s', cmdargs)
    stdout, stderr = subprocess.Popen(cmdargs,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()

    for line in stderr.splitlines():
        LOGGER.debug('ses_get_ed_metrics: sg_ses(stderr): %s', line)

    element_type = None
    descriptor = None

    for line in stdout.splitlines():
        LOGGER.debug('ses_get_ed_metrics: sg_ses: %s', line)
        if line and line[0] != ' ' and 'Element type:' in line:
            # Voltage  3.30V [6,0]  Element type: Voltage sensor
            mobj = re.search(r'([^\[]+)\[.*\][\s,]*Element type:\s*(.+)', line)
            if mobj:
                element_type = mobj.group(2).strip().replace(' ', '_')
                descriptor = mobj.group(1).strip()
                descriptor = descriptor.replace(' ', '_').replace('.', '_')
        else:
            yield element_type, descriptor, line.strip()

def ses_get_ed_metrics(sg_devname):
    """
    Return environment metrics as a dictionary from the SES Element
    Descriptor page.
    """
    for element_type, descriptor, line in _ses_get_ed_line(sg_devname):
        # Look for environment metrics
        mobj = re.search(r'(\w+)[:=]\s*([-+]*[0-9]+(\.[0-9]+)?)\s+(\w+)', line)
        if mobj:
            key, value, unit = mobj.group(1, 2, 4)
            yield dict((('element_type', element_type),
                        ('descriptor', descriptor), ('key', key),
                        ('value', value), ('unit', unit)))

def ses_get_ed_status(sg_devname):
    """
    Return different status code as a dictionary from the SES Element
    Descriptor page.
    """
    for element_type, descriptor, line in _ses_get_ed_line(sg_devname):
        # Look for status info
        mobj = re.search(r'status:\s*(.+)', line)
        if mobj:
            status = mobj.group(1).replace(' ', '_')
            yield dict((('element_type', element_type),
                        ('descriptor', descriptor), ('status', status)))
