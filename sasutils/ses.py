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

Requires sg3_utils.
"""

__author__ = 'sthiell@stanford.edu (Stephane Thiell)'

import re
import subprocess

class SESElementDescriptorMetricInfo(object):
    """Class to represent a SES Element descriptor metric."""

    def __init__(self, element_type, descriptor, key, unit, value):
        self.element_type = element_type
        self.descriptor = descriptor
        self.key = key
        self.unit = unit
        self.value = value

    def asdict(self):
        """Return a dict containing ed metric details."""
        # just use underlying __dict__
        return self.__dict__


def ses_get_snic_nickname(sg_devname):
    """Get subenclosure nickname (SES-2) [snic]"""
    # SES nickname is not available through sysfs, use sg_ses tool instead
    cmdargs = ['sg_ses', '--page=snic', '-I0', '/dev/' + sg_devname]
    stdout = subprocess.Popen(cmdargs,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
    for line in stdout.splitlines():
        mobj = re.match(r'\s+nickname:\s*([^ ]+)', line)
        if mobj:
            return mobj.group(1)

def ses_get_ed_metrics(sg_devname):
    """
    Return environment metrics (as SESElementDescriptorMetricInfo objects)
    from SES descriptor page.
    """
    cmdargs = ['sg_ses', '--page=ed', '--join', '/dev/' + sg_devname]
    stdout = subprocess.Popen(cmdargs,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE).communicate()[0]
    element_type = None
    descriptor = None
    for line in stdout.splitlines():
        if line[0] != ' ' and 'Element type:' in line:
            # Voltage  3.30V [6,0]  Element type: Voltage sensor
            mobj = re.search(r'([^\[]+)\[.*\][\s,]*Element type:\s*(.+)', line)
            if mobj:
                element_type = mobj.group(2).strip().replace(' ', '_')
                descriptor = mobj.group(1).strip()
                descriptor = descriptor.replace(' ', '_').replace('.', '_')
        else:
            line = line.strip()

            # Environment metrics
            mobj = re.search(r'(\w+)[:=]\s*([-+]*[0-9]+(\.[0-9]+)?)\s+(\w+)',
                             line)
            if mobj:
                key, value, unit = mobj.group(1, 2, 4)
                yield SESElementDescriptorMetricInfo(element_type, descriptor,
                                                     key, unit, value)
