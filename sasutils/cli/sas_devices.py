#!/usr/bin/python
#
# Copyright (C) 2016
#      The Board of Trustees of the Leland Stanford Junior University
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


from __future__ import print_function
import argparse
from itertools import ifilter
import socket

from sasutils.sas import SASHost, SASEndDevice
from sasutils.sysfs import sysfs
from sasutils.vpd import decode_vpd83_lu

#
# Main class for sas_list
#

class SASListCLI(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", action="store_true")
        self.args = parser.parse_args()

    def print_end_devices(self, sysfsnode):

        devmap = {}

        for node in sysfsnode:
            sas_end_device = SASEndDevice(node.node('device'))

            scsi_device = sas_end_device.scsi_device
            if hasattr(scsi_device, 'block'):
                pg83 = bytes(scsi_device.attrs.vpd_pg83)
                lu = decode_vpd83_lu(pg83)
                devmap.setdefault(lu, []).append(scsi_device.block)

        # list of set of enclosure
        encgroups = []

        for blklist in devmap.values():
            encs = set(blk.array_device.enclosure for blk in blklist)
            done = False
            for encset in encgroups:
                if not encset.isdisjoint(encs):
                    encset.update(encs)
                    done = True
                    break
            if not done:
                encgroups.append(encs)

        print("Found %s enclosure groups" % len(encgroups))

        for encset in encgroups:
            encinfolist = []
            for enc in encset:
                encinfolist.append('[%s %s, addr: %s]' % (enc.attrs.vendor,
                                                          enc.attrs.model,
                                                          enc.attrs.sas_address))
            print("Enclosure group: %s" % ''.join(encinfolist))
    
            cnt = 0
            for lu, devlist in ifilter(lambda (k, v): v[0].array_device.enclosure in encset,
                                       devmap.items()):
                blkdevs = ','.join(dev.name for dev in devlist)
                sgdevs = ','.join(dev.scsi_device.scsi_generic.sg_devname
                                  for dev in devlist)
                vendor = devlist[0].scsi_device.attrs.vendor
                model = devlist[0].scsi_device.attrs.model
                rev = devlist[0].scsi_device.attrs.rev
                print('  %10s %12s %12s %12s %12s %6s' % (lu, blkdevs, sgdevs,
                                                      vendor, model, rev))
                cnt += 1
            print("Total: %d block devices in enclosure group" % cnt)


def main():
    """console_scripts entry point for sas_discover command-line."""
    # start from /sys/class/sas_host
    root = sysfs.node('class').node('sas_end_device')
    SASListCLI().print_end_devices(root)

if __name__ == '__main__':
    main()
