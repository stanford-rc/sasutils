#
# Copyright (C) 2016, 2017, 2023
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

"""Build useful udev aliases for dm-multipath SAS array devices.

Each alias is built from the associated device SES-2 enclosure nickname
(must be set) and the array device bay identifier.

Example of udev rule:

KERNEL=="dm-[0-9]*", PROGRAM="/usr/bin/sas_mpath_snic_alias %k", SYMLINK+="mapper/%c"
"""

import logging
import os
import sys

from sasutils.sas import SASBlockDevice
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs

ALIAS_FORMAT = '{nickname}-bay{bay_identifier:02d}'


def sas_mpath_snic_alias(dmdev):
    """Use sasutils to get the alias name from the dm device."""

    # Principle:
    #   scan slaves block devices, for each:
    #     get bay identifier
    #     get enclosure device and its sg name
    #     get snic (subenclosure nickname)
    #   sanity: check if the bay identifers are the same
    #   find common snic part and return result

    snics = []
    bayids = []

    # dm's underlying sd* devices can easily be found in 'slaves'
    for node in sysfs.node('block').node(dmdev).node('slaves'):

        # Instantiate a block device object with SAS attributes
        blkdev = SASBlockDevice(node.node('device'))
        sasdev = blkdev.end_device.sas_device
        wwid = '%s_unknown' % dmdev

        # 'enclosure_device' symlink is present (preferred method)
        # Use array_device and enclosure to retrieve the ses sg name
        ses_sg = blkdev.scsi_device.array_device.enclosure.scsi_generic.sg_name
        try:
            # Use the wwid of the enclosure to create enclosure-specifc
            # aliases if an enclosure nickname is not set
            wwid = blkdev.scsi_device.array_device.enclosure.attrs.wwid
        except AttributeError:
            pass

        # Retrieve bay_identifier from matching sas_device
        bayids.append(int(sasdev.attrs.bay_identifier))

        # Get subenclosure nickname
        snic = ses_get_snic_nickname(ses_sg) or wwid
        snics.append(snic)

    if not bayids or not snics:
        return

    # assert that bay ids are the same...
    bay = bayids[0]
    assert bayids.count(bay) == len(bayids)

    snic = os.path.commonprefix(snics)
    snic = snic.rstrip('-_ ').replace(' ', '_')

    return ALIAS_FORMAT.format(nickname=snic, bay_identifier=bay)


def main():
    """Entry point for sas_mpath_snic_alias command-line."""
    if len(sys.argv) != 2:
        print('Usage: %s <dmdev>' % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    try:
        result = sas_mpath_snic_alias(sys.argv[1])
        if result:
            print(result)
    except KeyError as err:
        print("Not found: {0}".format(err), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
