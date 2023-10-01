#
# Copyright (C) 2023
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

"""Build a useful udev alias for a SAS tape drive attached to a SAS switch.

The alias is built from the associated enclosure nickname (must be set)
of the attached SAS switch and the array device bay identifier provided by
sysfs. Feel free to take this script as an example and adapt to your needs.

Example of udev rule:

KERNEL=="st*", PROGRAM="/usr/bin/sas_st_snic_alias %k", SYMLINK+="%c"
"""

import logging
import sys

from sasutils.sas import SASTapeDevice
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs

ALIAS_FORMAT = 'st-{nickname}-bay{bay_identifier:02d}'


def sas_st_snic_alias(stdev):
    """Use sasutils library to get the alias name from the tape device."""

    # Instantiate SCSITapeDevice object from scsi_tape device sysfs node
    #   eg. /sys/class/scsi_tape/st7
    tapedev = SASTapeDevice(sysfs.node('class').node('scsi_tape') \
                            .node(stdev).node('device'))
    sasdev = tapedev.end_device.sas_device

    wwid = '%s_unknown' % tapedev.name

    # 'enclosure_device' symlink is present (preferred method)
    # Use array_device and enclosure to retrieve the ses sg name
    ses_sg = tapedev.scsi_device.array_device.enclosure.scsi_generic.sg_name
    try:
        # Use the wwid of the enclosure to create enclosure-specifc
        # aliases if an enclosure nickname is not set
        wwid = tapedev.scsi_device.array_device.enclosure.attrs.wwid
    except AttributeError:
        pass

    # Retrieve bay_identifier from matching sas_device
    bay = int(sasdev.attrs.bay_identifier)

    # Get subenclosure nickname
    snic = ses_get_snic_nickname(ses_sg) or wwid

    return ALIAS_FORMAT.format(nickname=snic, bay_identifier=bay)


def main():
    """Entry point for sas_st_snic_alias command-line."""
    if len(sys.argv) != 2:
        print('Usage: %s <stdev>' % sys.argv[0], file=sys.stderr)
        sys.exit(1)
    try:
        result = sas_st_snic_alias(sys.argv[1])
        if result:
            print(result)
    except KeyError as err:
        print("Not found: {0}".format(err), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
