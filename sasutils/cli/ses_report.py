#!/usr/bin/python
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


"""
ses_report - SES status and metrics reporting utility
"""


from __future__ import print_function
import time

from sasutils.sas import SASExpander
from sasutils.scsi import TYPE_ENCLOSURE
from sasutils.ses import ses_get_ed_metrics, ses_get_snic_nickname
from sasutils.sysfs import sysfs


def main():
    """console_scripts entry point for the ses_report command-line."""
    for node in sysfs.node('class').node('sas_expander'):
        expander = SASExpander(node.node('device'))
        for end_device in expander.end_devices_by_scsi_type(TYPE_ENCLOSURE):
            # Get enclosure SG device
            sg_dev = end_device.scsi_device.scsi_generic
            # Resolve SES enclosure nickname
            snic = ses_get_snic_nickname(sg_dev.name).replace(' ', '_')
            if not snic:
                # Use Vendor + SAS address if SES encl. nickname not defined
                snic = end_device.scsi_device.attrs.vendor.replace(' ', '-')
                snic += '_' + end_device.scsi_device.attrs.sas_address
            time_now = time.time()
            for edinfo in ses_get_ed_metrics(sg_dev.name):
                # print output in a Graphite compatible format
                carbon_fmt = '{element_type}.{descriptor}.{key}_{unit} {value}'
                carbon_path = carbon_fmt.format(**edinfo.asdict())
                print('%s.%s %d' % (snic, carbon_path, time_now))


if __name__ == '__main__':
    main()
