#
# Copyright (C) 2016, 2017
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


from __future__ import print_function
import argparse
from collections import namedtuple
from itertools import groupby
from operator import attrgetter
import struct
import sys
import re

from sasutils.sas import SASHost, SASExpander, SASEndDevice
from sasutils.scsi import EnclosureDevice
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs
from sasutils.vpd import vpd_decode_pg83_lu, vpd_get_page83_lu
from sasutils.vpd import vpd_get_page80_sn


class SASDevicesCLI(object):
    """Main class for sas_devises command-line interface."""

    HDR_DEVLIST_VERB = {'bay': 'BAY', 'lu': 'LOGICAL UNIT',
                        'dm': 'DEVICE MAPPER', 'paths': 'PATHS',
                        'blkdevs': 'BLOCK_DEVS', 'sgdevs': 'SG_DEVS',
                        'vendor': 'VENDOR', 'model': 'MODEL', 'rev': 'REV',
                        'pg80': 'SERIAL_NUMBER', 'blk_sz_info': 'SIZE'}
    FMT_DEVLIST_VERB = '{bay:>3} {lu:>18} {dm:>18} {blkdevs:>12} ' \
                       '{sgdevs:>12} {paths:>5} {vendor:>8} {model:>16} ' \
                       '{pg80:>22} {rev:>8} {blk_sz_info}'

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', '-v', action='count', default=0,
                            help='Verbosity level, repeat multiple times!')
        self.args = parser.parse_args()

    def print_hosts(self, sysfsnode):
        sas_hosts = []
        for sas_host in sysfsnode:
            sas_hosts.append(SASHost(sas_host.node('device')))

        msgstr = "Found %d SAS hosts" % len(sas_hosts)
        if self.args.verbose > 0:
            print("%s: %s" % (msgstr,
                              ','.join(host.name for host in sas_hosts)))
        else:
            print(msgstr)

    def print_expanders(self, sysfsnode):
        sas_expanders = []
        for expander in sysfsnode:
            sas_expanders.append(SASExpander(expander.node('device')))

        # Find unique expander thanks to their sas_address
        attrname = 'sas_device.attrs.sas_address'
        # Sort the expander list before using groupby()
        sas_expanders = sorted(sas_expanders, key=attrgetter(attrname))
        # Group expanders by SAS address
        num_exp = 0
        for addr, expgroup in groupby(sas_expanders, attrgetter(attrname)):
            if self.args.verbose > 0:
                exps = list(expgroup)
                explist = ','.join(exp.name for exp in exps)
                print('SAS expander %s x%d (%s)' % (addr, len(exps), explist))
            num_exp += 1
        print("Found %d SAS expanders" % num_exp)

    def _get_dev_attrs(self, sas_end_device, scsi_device, with_sn=True):
        # Vendor info
        res = {'vendor': scsi_device.attrs.vendor,
               'model': scsi_device.attrs.model,
               'rev': scsi_device.attrs.rev}

        # Size of block device
        blk_sz = scsi_device.block.sizebytes()
        if blk_sz >= 1e12:
            blk_sz_info = "%.1fTB" % (blk_sz / 1e12)
        else:
            blk_sz_info = "%.1fGB" % (blk_sz / 1e9)
        res['blk_sz_info'] = blk_sz_info

        if with_sn:
            # Device Mapper name
            res['dm'] = scsi_device.block.dm()

            # Bay identifier
            try:
                res['bay'] = int(sas_end_device.sas_device.attrs.bay_identifier)
            except (AttributeError, ValueError):
                pass

            # Serial number
            try:
                pg80 = scsi_device.attrs.vpd_pg80
                res['pg80'] = pg80[4:].decode("utf-8", errors='backslashreplace')
            except AttributeError:
                pg80 = vpd_get_page80_sn(scsi_device.block.name)
                res['pg80'] = pg80

        return res

    def _print_lu_devlist(self, lu, devlist, maxpaths=None):
        if self.args.verbose > 1:
            for _, scsi_dev in devlist:
                print("Info: %s: %s" % (scsi_dev.__class__.__name__,
                                        scsi_dev.sysfsnode.path))

        # use the first device for the following common attributes
        info = self._get_dev_attrs(*devlist[0])

        info['lu'] = lu
        info['blkdevs'] = ','.join(scsi_device.block.name
                                   for sas, scsi_device in devlist)
        info['sgdevs'] = ','.join(scsi_device.scsi_generic.sg_name
                                  for sas, scsi_device in devlist)

        # Number of paths
        paths = "%d" % len(devlist)
        if maxpaths and len(devlist) < maxpaths:
            paths += "*"
        info['paths'] = paths
        info.setdefault('bay', '-')
        print(self.FMT_DEVLIST_VERB.format(**info))

    def print_end_devices(self, sysfsnode):
        # This code is ugly and should be rewritten...
        devmap = {}  # LU -> list of (SASEndDevice, SCSIDevice)

        for node in sysfsnode:
            sas_end_device = SASEndDevice(node.node('device'))

            for scsi_device in sas_end_device.targets:
                if scsi_device.block:
                    try:
                        try:
                            pg83 = bytes(scsi_device.attrs.vpd_pg83)
                        except TypeError:
                            pg83 = bytes(scsi_device.attrs.vpd_pg83,
                                         encoding='utf-8')
                        lu = vpd_decode_pg83_lu(pg83)
                    except (AttributeError, struct.error):
                        lu = vpd_get_page83_lu(scsi_device.block.name)
                    except TypeError:
                        lu = 'Error-%s' % scsi_device.block.name
                        print('Error: %s vpd_pg83="%s"' % (scsi_device.block,
                              scsi_device.attrs.vpd_pg83), file=sys.stderr)

                    devmap.setdefault(lu, []).append((sas_end_device,
                                                      scsi_device))

        # list of set of enclosure
        encgroups = []

        for lu, dev_list in devmap.items():
            encs = set()
            for sas_ed, scsi_device in dev_list:
                blk = scsi_device.block
                assert blk
                if blk.array_device:
                    # 'enclosure_device' symlink is present (preferred method)
                    encs.add(blk.array_device.enclosure)
                    if self.args.verbose > 1:
                        print("Info: found enclosure device %s for block device %s" \
                              % (blk.array_device.enclosure.sysfsnode.path,
                                 blk.sysfsnode.path))
                else:
                    encs.add(None)
                    print("Warning: no enclosure symlink set for %s in %s" %
                          (blk.name, blk.scsi_device.sysfsnode.path))
            done = False
            for encset in encgroups:
                if not encset.isdisjoint(encs):
                    encset.update(encs)
                    done = True
                    break
            if not done:
                encgroups.append(encs)

        print("Found %d enclosure groups" % len(encgroups))

        for encset in encgroups:
            encinfolist = []

            def kfun(o):
                if o:
                    return int(re.sub("\D", "", o.scsi_generic.name))
                else:
                    return -1

            def enclosure_finder(arg):
                _lu, _dev_list = arg
                for _sas_ed, _scsi_device in _dev_list:
                    _blk = _scsi_device.block
                    assert _blk
                    if _blk.array_device:
                        # 'enclosure_device' symlink is present
                        if _blk.array_device.enclosure in encset:
                            return True
                return False

            def enclosure_absent(arg):
                _lu, _dev_list = arg
                for _sas_ed, _scsi_device in _dev_list:
                    _blk = _scsi_device.block
                    assert _blk
                    if _blk.array_device:
                        # 'enclosure_device' symlink is present
                        if _blk.array_device.enclosure:
                            return False
                return True

            has_orphans = False
            for enc in sorted(encset, key=kfun):
                if enc:
                    snic = ses_get_snic_nickname(enc.scsi_generic.name)
                    if snic:
                        if self.args.verbose > 0:
                            encinfolist.append('[%s:%s]' % (enc.scsi_generic.name,
                                                            snic))
                        else:
                            encinfolist.append('[%s]' % snic)
                    else:
                        if self.args.verbose > 0:
                            vals = (enc.scsi_generic.name, enc.attrs.vendor,
                                    enc.attrs.model, enc.attrs.sas_address)
                            encinfolist.append('[%s:%s %s, addr: %s]' % vals)
                        else:
                            vals = (enc.attrs.vendor, enc.attrs.model,
                                    enc.attrs.sas_address)
                            encinfolist.append('[%s %s, addr: %s]' % vals)
                else:
                    has_orphans = True
                    encinfolist.append('[**orphans found**]')

            encdevs = []
            if has_orphans:
                encdevs = list(filter(enclosure_absent, devmap.items()))

            if not encdevs:
                encdevs = list(filter(enclosure_finder, devmap.items()))

            print("Enclosure group: %s" % ''.join(encinfolist))

            maxpaths = max(len(devs) for lu, devs in encdevs)

            cnt = 0

            if self.args.verbose > 0:
                print(self.FMT_DEVLIST_VERB.format(**self.HDR_DEVLIST_VERB))

                def kfun(o):
                    try:
                        return int(o[1][0][0].sas_device.attrs.bay_identifier)
                    except ValueError:
                        return -1
                for lu, devlist in sorted(encdevs, key=kfun):
                    self._print_lu_devlist(lu, devlist, maxpaths)
                    cnt += 1
            else:
                folded = {}
                for lu, devlist in encdevs:
                    # try to regroup disks by getting common attributes
                    devinfo = self._get_dev_attrs(*devlist[0], with_sn=False)
                    devinfo['paths'] = len(devlist)
                    folded_key = namedtuple('FoldedDict',
                                            devinfo.keys())(**devinfo)
                    folded.setdefault(folded_key, []).append(devlist)
                    cnt += 1
                print("NUM   %12s %16s %6s %8s %6s" % ('VENDOR', 'MODEL', 'REV',
                                                       'SIZE', 'PATHS'))
                for t, v in folded.items():
                    if maxpaths and t.paths < maxpaths:
                        pathstr = '%s*' % t.paths
                    else:
                        pathstr = '%s ' % t.paths
                    infofmt = '{vendor:>12} {model:>16} {rev:>6} {blk_sz_info:>8} {paths:>6}'
                    infostr = infofmt.format(**t._asdict())
                    print('%3d x %s' % (len(v), infostr))
            print("Total: %d block devices in enclosure group" % cnt)


def main():
    """console_scripts entry point for sas_devices command-line."""

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
