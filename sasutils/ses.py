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
