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


import argparse
from collections import namedtuple, OrderedDict
from itertools import groupby
from operator import attrgetter
from string import Formatter
import re
import struct
import sys
import time

from sasutils.sas import SASHost, SASExpander, SASEndDevice
from sasutils.scsi import EnclosureDevice, strtype, TYPE_ENCLOSURE
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs
from sasutils.vpd import vpd_decode_pg83_lu, vpd_get_page83_lu
from sasutils.vpd import vpd_get_page80_sn


# header keywords
FMT_MAP = { 'bay': 'BAY',
            'blkdevs': 'BLOCK_DEVS',
            'dm': 'DEVICE_MAPPER',
            'model': 'MODEL',
            'paths': 'PATHS',
            'rev': 'REV',
            'sgdevs': 'SG_DEVS',
            'stdevs': 'ST_DEVS',
            'size': 'SIZE',
            'sn': 'SERIAL_NUMBER',
            'snic': 'NICKNAME',
            'state': 'STATE',
            'target': 'TARGET',
            'timeout': 'TIMEOUT',
            'type': 'TYPE',
            'vendor': 'VENDOR',
            'wwid': 'WWID' }

# default format string
DEF_FMT = '{type:>10} {vendor:>12} {model:>16} {rev:>6} {size:>7} ' \
          '{paths:>6} {state:>9}'

# default format string in verbose mode
DEF_FMT_VERB = '{bay:>3} {type:>10} {wwid:>24} {snic:>16} {dm:>18} ' \
               '{blkdevs:>12} {stdevs:>8} {sgdevs:>12} {paths:>5} ' \
               '{vendor:>8} {model:>16} {sn:>20} {rev:>8} {size:>7} ' \
               '{target:>10} {state:>8}'


class SASDevicesCLI(object):
    """Main class for sas_devises command-line interface."""

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--quiet', '-q', action='store_true',
                            help='Straight to the point')
        parser.add_argument('--verbose', '-v', action='count', default=0,
                            help='Verbosity level, repeat multiple times!')
        parser.add_argument('--format', '-o', action='store', default=DEF_FMT,
                            help='Specify  the  information  to be displayed' \
                                 ' (default: "%s" or "%s" with -v)' % (DEF_FMT, DEF_FMT_VERB))
        self.args = parser.parse_args()
        if self.args.verbose > 0 and self.args.format is DEF_FMT:
            self.args.format = DEF_FMT_VERB

        if self.args.verbose > 1:
            print('FORMAT: "%s"' % self.args.format)

        self.fields = OrderedDict()

        for _, field, fmt_spec, _ in Formatter().parse(self.args.format):
            if field:
                if field in FMT_MAP:
                    self.fields[field] = fmt_spec
                else:
                    parser.error('Unknown format field "%s"' % field)
        if not self.fields:
            parser.error('No valid field found in format string')

    def print_hosts(self, sysfsnode):
        total = len(sysfsnode)
        tslen = len(str(total))
        maxlen = num = 0
        sas_hosts = []
        for sas_host in sysfsnode:
            num += 1
            if not self.args.quiet:
                towrite = '%s: %*d/%*d\r' % (sysfsnode, tslen, num, tslen, total)
                maxlen = max(len(towrite), maxlen)
                sys.stderr.write(towrite)
            sas_hosts.append(SASHost(sas_host.node('device')))
        if not self.args.quiet:
            sys.stderr.write(' ' * maxlen + '\r')
        msgstr = "Found %d SAS hosts" % len(sas_hosts)
        if self.args.verbose > 1:
            print("%s: %s" % (msgstr,
                              ','.join(host.name for host in sas_hosts)))
        elif self.args.verbose > 0:
            print(msgstr)

    def print_expanders(self, sysfsnode):
        total = len(sysfsnode)
        tslen = len(str(total))
        maxlen = num = 0
        sas_expanders = []
        for expander in sysfsnode:
            num += 1
            if not self.args.quiet:
                towrite = '%s: %*d/%*d\r' % (sysfsnode, tslen, num, tslen, total)
                maxlen = max(len(towrite), maxlen)
                sys.stderr.write(towrite)
            sas_expanders.append(SASExpander(expander.node('device')))

        # Find unique expander thanks to their sas_address
        attrname = 'sas_device.attrs.sas_address'
        # Sort the expander list before using groupby()
        sas_expanders = sorted(sas_expanders, key=attrgetter(attrname))
        # Group expanders by SAS address
        num_exp = 0
        for addr, expgroup in groupby(sas_expanders, attrgetter(attrname)):
            if self.args.verbose > 1:
                exps = list(expgroup)
                explist = ','.join(exp.name for exp in exps)
                print('SAS expander %s x%d (%s)' % (addr, len(exps), explist))
            num_exp += 1

        if not self.args.quiet:
            sys.stderr.write(' ' * maxlen + '\r')
        if self.args.verbose > 0:
            print("Found %d SAS expanders" % num_exp)

    def _get_dev_attrs(self, sas_end_device, scsi_device):
        res = {}

        # scsi_device

        for key in ('model', 'rev', 'state', 'timeout', 'vendor'):
            res[key] = ''
            if key in self.fields:
                try:
                    res[key] = getattr(scsi_device.attrs, key)
                except AttributeError as exc:
                    print('ERROR: %s: %s' % (scsi_device, exc), file=sys.stderr)
                    res[key] = '<error>'

        if 'target' in self.fields:
            res['target'] = ''
            try:
                res['target'] = str(scsi_device.sysfsnode)
            except AttributeError as exc:
                print('ERROR: %s: %s' % (scsi_device, exc), file=sys.stderr)
                res['target'] = '<error>'

        if 'type' in self.fields:
            res['type'] = ''
            try:
                res['type'] = scsi_device.strtype
            except AttributeError as exc:
                print('ERROR: %s: %s' % (scsi_device, exc), file=sys.stderr)
                res['type'] = '<error>'

        # size of block device
        if 'size' in self.fields:
            res['size'] = ''
            # Size of block device
            if scsi_device.block:
                try:
                    blk_sz = scsi_device.block.sizebytes()
                    if blk_sz >= 1e12:
                        blk_sz_info = "%.1fTB" % (blk_sz / 1e12)
                    else:
                        blk_sz_info = "%.1fGB" % (blk_sz / 1e9)
                    res['size'] = blk_sz_info
                except AttributeError as exc:
                    print('ERROR: %s: %s' % (scsi_device, exc), file=sys.stderr)
                    res['size'] = '<error>'

        # Device Mapper name
        if 'dm' in self.fields:
            res['dm'] = ''
            if scsi_device.block:
                try:
                    res['dm'] = scsi_device.block.dm()
                except (AttributeError, ValueError):
                    pass

        # Bay identifier
        if 'bay' in self.fields:
            res['bay'] = ''
            try:
                res['bay'] = int(sas_end_device.sas_device.attrs.bay_identifier)
            except (AttributeError, ValueError):
                pass

        if 'sn' in self.fields:
            res['sn'] = ''
            # Serial number
            try:
                pg80 = scsi_device.attrs.vpd_pg80
                res['sn'] = pg80[4:].decode("utf-8", errors='backslashreplace')
            except AttributeError:
                if scsi_device.block:
                    pg80 = vpd_get_page80_sn(scsi_device.block.name)
                    res['sn'] = pg80
            res['sn'] = res['sn'].strip()

        # SES Subenclosure nickname
        if 'snic' in self.fields:
            snic = None
            if int(scsi_device.attrs.type) == TYPE_ENCLOSURE:
                snic = ses_get_snic_nickname(scsi_device.scsi_generic.name)
            res['snic'] = snic or ''

        return res

    def _get_devlist_attrs(self, wwid, devlist, maxpaths=None):
        # use the first device for the following common attributes
        res = self._get_dev_attrs(*devlist[0])

        if 'wwid' in self.fields:
            res['wwid'] = wwid

        if 'blkdevs' in self.fields:
            res['blkdevs'] = ','.join(scsi_device.block.name
                                       for sas, scsi_device in devlist
                                       if scsi_device.block)
        if 'sgdevs' in self.fields:
            res['sgdevs'] = ','.join(scsi_device.scsi_generic.sg_name
                                      for sas, scsi_device in devlist)
        if 'stdevs' in self.fields:
            res['stdevs'] = ','.join(scsi_device.tape.name
                                       for sas, scsi_device in devlist
                                       if scsi_device.tape)

        if 'paths' in self.fields:
            # Number of paths
            paths = "%d" % len(devlist)
            if maxpaths and len(devlist) < maxpaths:
                paths += "*"
            res['paths'] = paths

        return res

    def print_end_devices(self, sysfsnode):
        total = len(sysfsnode)
        tslen = len(str(total))
        maxlen = num = 0

        # This code is ugly and should be rewritten...
        devmap = {}  # LU -> list of (SASEndDevice, SCSIDevice)

        for node in sysfsnode:
            num += 1
            if not self.args.quiet:
                towrite = '%s: %*d/%*d\r' % (sysfsnode, tslen, num, tslen, total)
                maxlen = max(len(towrite), maxlen)
                sys.stderr.write(towrite)

            sas_end_device = SASEndDevice(node.node('device'))

            for scsi_device in sas_end_device.targets:
                if self.args.verbose > 1:
                    print("Device: %s" % scsi_device.sysfsnode.path)

                wwid = scsi_device.attrs.wwid
                if not wwid:
                    if scsi_device.block:
                        try:
                            try:
                                pg83 = bytes(scsi_device.attrs.vpd_pg83)
                            except TypeError:
                                pg83 = bytes(scsi_device.attrs.vpd_pg83,
                                             encoding='utf-8')
                            wwid = vpd_decode_pg83_lu(pg83)
                        except (AttributeError, struct.error):
                            wwid = vpd_get_page83_lu(scsi_device.block.name)
                        except TypeError:
                            wwid = 'Error-%s' % scsi_device.block.name
                            print('Error: %s vpd_pg83="%s"' % (scsi_device.block,
                                  scsi_device.attrs.vpd_pg83), file=sys.stderr)

                        devmap.setdefault(wwid, []).append((sas_end_device,
                                                            scsi_device))
                    else:
                        print('Error: no wwid for %s' % scsi_device.sysfsnode.path,
                              file=sys.stderr)
                        wwid = 'Error-%s' % scsi_device.sysfsnode
                if wwid.startswith('[Errno'):
                    wwid = wwid.split(']')[0] + ']'
                devmap.setdefault(wwid, []).append((sas_end_device, scsi_device))

        if not self.args.quiet:
            sys.stderr.write(' ' * maxlen + '\r')
        if self.args.verbose > 0:
            print("Found %d SAS end devices" % num)

        # list of set of enclosure
        encgroups = []

        for lu, dev_list in devmap.items():
            encs = set()
            for sas_ed, scsi_device in dev_list:
                if scsi_device.array_device:
                    # 'enclosure_device' symlink is present (preferred method)
                    encs.add(scsi_device.array_device.enclosure)
                    if self.args.verbose > 1:
                        print("Info: found enclosure device %s for device %s" \
                              % (scsi_device.array_device.enclosure.sysfsnode.path,
                                 scsi_device.sysfsnode.path))
                else:
                    encs.add(None)
                    if self.args.verbose > 1:
                        print("Info: no enclosure symlink set for %s in %s" %
                              (scsi_device.name, scsi_device.sysfsnode.path))
            done = False
            for encset in encgroups:
                if not encset.isdisjoint(encs):
                    encset.update(encs)
                    done = True
                    break
            if not done:
                encgroups.append(encs)

        sys.stderr.write(' ' * maxlen + '\r')
        num_encgroups = len([enc for enc in encgroups if list(enc)[0]])
        if self.args.verbose > 0:
            if num_encgroups > 0:
                print("Resolved %d enclosure groups" % num_encgroups)
            else:
                print("No enclosure found")

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
                    if _scsi_device.array_device:
                        # 'enclosure_device' symlink is present
                        if _scsi_device.array_device.enclosure in encset:
                            return True
                return False

            def enclosure_absent(arg):
                _lu, _dev_list = arg
                for _sas_ed, _scsi_device in _dev_list:
                    if _scsi_device.array_device:
                        # 'enclosure_device' symlink is present
                        if _scsi_device.array_device.enclosure:
                            return False
                return True

            has_orphans = False
            for enc in sorted(encset, key=kfun):
                if enc:
                    snic = ses_get_snic_nickname(enc.scsi_generic.name)
                    if snic:
                        if self.args.verbose > 0:
                            encinfolist.append('[%s:%s, addr: %s]' %
                                               (enc.scsi_generic.name,
                                                snic, enc.attrs.sas_address))
                        else:
                            encinfolist.append('[%s:%s]' % (enc.scsi_generic.name,
                                                            snic))
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

            encdevs = []
            if has_orphans:
                encdevs = list(filter(enclosure_absent, devmap.items()))

            if not encdevs:
                encdevs = list(filter(enclosure_finder, devmap.items()))

            maxpaths = max(len(devs) for lu, devs in encdevs)

            def kfun(o):
                try:
                    return int(o[1][0][0].sas_device.attrs.bay_identifier)
                except ValueError:
                    return -1

            cnt = 0
            grp_format = self.args.format
            field_trckr = {}
            folded = {}
            for lu, devlist in sorted(encdevs, key=kfun):
                devinfo = self._get_devlist_attrs(lu, devlist)
                # try to regroup devices by getting common attributes
                devinfo['paths'] = len(devlist)
                folded_key = namedtuple('FoldedDict',
                                        devinfo.keys())(**devinfo)
                folded.setdefault(folded_key, []).append(devlist)
                used = False
                for field in self.fields:
                    if devinfo.get(field):
                        field_trckr[field] = field_trckr.setdefault(field, 0) + 1
                        if not used:
                            used = True
                            cnt += 1

            # remove unused columns
            for field in self.fields:
                fcnt = field_trckr.get(field, 0)
                if fcnt == 0:
                    grp_format = re.sub('\s*\{%s.*?\}\s*' % field, ' ',
                                        grp_format)

            if cnt > 0:
                if has_orphans:
                    print("*** Standalone devices")
                else:
                    print("*** Enclosure group: %s" % ''.join(encinfolist))

                hdrfmt = '      ' + grp_format
                print(hdrfmt.format(**FMT_MAP))

                for t, v in folded.items():
                    if maxpaths and t.paths < maxpaths:
                        pathstr = '%s*' % t.paths
                    else:
                        pathstr = '%s ' % t.paths

                    infostr = grp_format.format(**t._asdict())

                    if self.args.verbose > 1:
                        for devlist in v:
                            for _, scsi_dev in devlist:
                                print("Info: %s: %s" % (scsi_dev.__class__.__name__,
                                                        scsi_dev.sysfsnode.path))

                    if len(v) > 1:
                        print('%3d x %s' % (len(v), infostr))
                    else:
                        print('      %s' % infostr)

                if not self.args.quiet:
                    print("Total: %d devices" % cnt)


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
