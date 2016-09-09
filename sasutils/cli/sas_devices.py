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
import sys

from sasutils.sas import SASHost, SASExpander, SASEndDevice
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs
from sasutils.vpd import decode_vpd83_lu, vpd_get_page83_lu


class SASDevicesCLI(object):
    """Main class for sas_devises command-line interface."""

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", action="store_true")
        self.args = parser.parse_args()

    def print_hosts(self, sysfsnode):
        sas_hosts = []
        for sas_host in sysfsnode:
            sas_hosts.append(SASHost(sas_host.node('device')))

        msgstr = "Found %d SAS hosts" % len(sas_hosts)
        if self.args.verbose:
            print("%s: %s" % (msgstr,
                              ','.join(host.name for host in sas_hosts)))
        else:
            print(msgstr)

    def print_expanders(self, sysfsnode):
        sas_expanders = []
        for expander in sysfsnode:
            sas_expanders.append(SASExpander(expander.node('device')))

        msgstr = "Found %d SAS expanders" % len(sas_expanders)
        if self.args.verbose:
            print("%s: %s" % (msgstr,
                              ','.join(exp.name for exp in sas_expanders)))
        else:
            print(msgstr)

    def _print_lu_devlist(self, lu, devlist, maxpaths=None):
        blkdevs = ','.join(dev.name for dev in devlist)
        sgdevs = ','.join(dev.scsi_device.scsi_generic.sg_devname
                          for dev in devlist)
        vendor = devlist[0].scsi_device.attrs.vendor
        model = devlist[0].scsi_device.attrs.model
        rev = devlist[0].scsi_device.attrs.rev
        paths = "%d" % len(devlist)
        if maxpaths and len(devlist) < maxpaths:
            paths += "*"
        print('  %10s %12s %12s %-3s %10s %10s %6s' % (lu, blkdevs, sgdevs, paths,
                                                  vendor, model, rev))

    def print_end_devices(self, sysfsnode):

        devmap = {}

        for node in sysfsnode:
            sas_end_device = SASEndDevice(node.node('device'))

            scsi_device = sas_end_device.scsi_device
            if hasattr(scsi_device, 'block'):
                try:
                    pg83 = bytes(scsi_device.attrs.vpd_pg83)
                    lu = decode_vpd83_lu(pg83)
                except AttributeError:
                    lu = vpd_get_page83_lu(scsi_device.block.name)

                devmap.setdefault(lu, []).append(scsi_device.block)

        # list of set of enclosure
        encgroups = []
        orphans = []

        for lu, blklist in devmap.items():
            for blk in blklist:
                if blk.array_device is None:
                    print("Warning: no enclosure set for %s in %s" %
                          (blk.name, blk.scsi_device.sysfsnode.path))
            encs = set(blk.array_device.enclosure
                       for blk in blklist
                       if blk.array_device is not None)
            if not encs:
                orphans.append((lu, blklist))
                continue
            done = False
            for encset in encgroups:
                if not encset.isdisjoint(encs):
                    encset.update(encs)
                    done = True
                    break
            if not done:
                encgroups.append(encs)

        print("Found %d enclosure groups" % len(encgroups))
        if orphans:
            print("Found %d orphan devices" % len(orphans))

        for encset in encgroups:
            encinfolist = []
            for enc in sorted(encset):
                snic = ses_get_snic_nickname(enc.scsi_generic.name)
                if snic:
                    encinfolist.append('[%s]' % snic)
                else:
                    encinfolist.append('[%s %s, addr: %s]' % (enc.attrs.vendor,
                                                              enc.attrs.model,
                                                              enc.attrs.sas_address))

            print("Enclosure group: %s" % ''.join(encinfolist))

            cnt = 0

            def enclosure_finder((lu, blklist)):
                for blk in blklist:
                    if blk.array_device and blk.array_device.enclosure in encset:
                        return True
                return False

            encdevs = list(ifilter(enclosure_finder, devmap.items()))
            maxpaths = max(len(devs) for lu, devs in encdevs)

            if self.args.verbose:
                for lu, devlist in encdevs:
                    self._print_lu_devlist(lu, devlist, maxpaths)
                    cnt += 1
            else:
                folded = {}
                for lu, devlist in encdevs:
                    vendor = devlist[0].scsi_device.attrs.vendor
                    model = devlist[0].scsi_device.attrs.model
                    rev = devlist[0].scsi_device.attrs.rev
                    paths = len(devlist)
                    folded.setdefault((vendor, model, rev, paths), []).append(devlist)
                    cnt += 1
                print("NUM   %12s %12s %6s %5s"  % ('VENDOR', 'MODEL', 'REV', 'PATHS'))
                for (vendor, model, rev, paths), v in folded.items():
                    if maxpaths and paths < maxpaths:
                        pathstr = '%s*' % paths
                    else:
                        pathstr = '%s ' % paths
                    print("%3d x %12s %12s %6s %5s" % (len(v), vendor, model, rev, pathstr))
            print("Total: %d block devices in enclosure group" % cnt)

        if orphans:
            print("Orphan devices:")
        for lu, blklist in orphans:
            self._print_lu_devlist(lu, blklist)


def main():
    """console_scripts entry point for sas_discover command-line."""

    sas_devices_cli = SASDevicesCLI()

    try:
        root = sysfs.node('class').node('sas_host')
        sas_devices_cli.print_hosts(root)
        root = sysfs.node('class').node('sas_expander')
        sas_devices_cli.print_expanders(root)
        root = sysfs.node('class').node('sas_end_device')
        sas_devices_cli.print_end_devices(root)
    except KeyError as err:
        print("Not found: %s" % err, file=sys.stderr)

if __name__ == '__main__':
    main()
