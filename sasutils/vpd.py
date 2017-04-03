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

# Inspired from decode_dev_ids() in sg3_utils/src/sg_vpd.c

from struct import unpack_from
import subprocess

__author__ = 'sthiell@stanford.edu (Stephane Thiell)'


def vpd_decode_pg83_lu(pagebuf):
    """
    Get the addressed logical unit address from the device identification
    VPD page buffer provided (eg. content of vpd_pg83 in sysfs).
    """
    vpd_assoc_lu = 0
    sz = len(pagebuf)
    offset = 4
    d, = unpack_from('B', pagebuf, offset + 2)
    assert d == 0, 'skip_1st_iter not implemented'
    while True:
        code_set, = unpack_from('B', pagebuf, offset)
        d, = unpack_from('B', pagebuf, offset + 1)
        design_type = (d & 0xf)
        assoc = (d >> 4) & 0x3
        d, = unpack_from('B', pagebuf, offset + 3)
        next_offset = offset + (d & 0xf) + 4
        if next_offset > sz:
            break

        if design_type == 3 and assoc == vpd_assoc_lu:
            d, = unpack_from('B', pagebuf, offset + 4)
            naa = (d >> 4) & 0xff
            return '0x' + ''.join("%02x" % i
                                  for i in unpack_from('BBBBBBBB',
                                                       pagebuf, offset + 4))
        offset = next_offset


#
# Support for RHEL/CentOS 6 (missing sysfs vpd_pg80 and vpd_pg83)
#
def vpd_get_page80_sn(blkdev):
    """
    Get page 0x80 Serial Number using external command.
    """
    cmdargs = ['scsi_id', '--page=0x80', '--whitelisted',
               '--device=/dev/' + blkdev]
    output = subprocess.Popen(cmdargs, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("utf-8").rstrip().split()[-1]


def vpd_get_page83_lu(blkdev):
    """
    Get page 0x83 Logical Unit using external command.
    """
    cmdargs = ['scsi_id', '--page=0x83', '--whitelisted',
               '--device=/dev/' + blkdev]
    output = subprocess.Popen(cmdargs, stdout=subprocess.PIPE).communicate()[0]
    return output.decode("utf-8").rstrip()
