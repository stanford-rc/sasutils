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


import argparse
import ast
from itertools import groupby
import socket
import sys

from collections import Counter
from sasutils.sas import SASHost
from sasutils.ses import ses_get_snic_nickname
from sasutils.scsi import TYPE_ENCLOSURE
from sasutils.sysfs import sysfs


def format_attrs(attrlist, attrs):
    """filter keys to avoid SysfsObject cache miss on all attrs"""
    attr_fmt = ('%s: {%s}' % t for t in attrlist)
    iargs = dict((k, attrs.get(k, 'N/A')) for _, k in attrlist)
    return ', '.join(attr_fmt).format(**iargs)


class SDNode(object):
    gatherme = False

    def __init__(self, name, baseobj, nphys=0, speedstr='', depth=0, disp=None,
                 prinfo=None):
        self.name = name
        self.baseobj = baseobj
        self.children = []
        self.speedstr = speedstr
        self.nphys = nphys
        self.depth = depth
        self.disp = disp
        self.prinfo = prinfo or []
        self.proffset = 0  # prompt offset; derived classes may override
        self._prompt = None
        self.resolve()

    def resolve(self):
        pass

    def __str__(self):
        return self.name

    def gathergrp(self):
        return None

    #
    # Helpers for text-based representation of the tree topology
    #
    def gen_prompt(self, prinfo=None):
        prompt = []
        if not prinfo:
            prinfo = self.prinfo
        pilen = len(prinfo)
        for index, (plink, plen) in enumerate(prinfo):
            if plink == ' ':
                prompt.append(' ' * plen + plink + '  ')
            else:
                if index == pilen - 1:
                    prompt.append(' ' * plen + plink + '--')
                else:
                    prompt.append(' ' * plen + plink + '  ')
            if plink == '`':
                prinfo[index] = (' ', plen)
        return ''.join(prompt)

    def adv_prompt(self, offset=0, last=False):
        self.prompt  # ensure current prompt is generated
        if last:
            plink = '`'
        else:
            plink = '|'
        return self.prinfo + [(plink, offset)]

    @property
    def prompt(self):
        if not self._prompt:
            self._prompt = self.gen_prompt()
        return self._prompt

    def add_child(self, sdclass, baseobj, name=None, nphys=0, speedstr='', last=False):
        if not name:
            baseobjname = baseobj.name  # mandatory when name not provided
        else:
            baseobjname = name
        self.children.append(sdclass(baseobjname, baseobj, nphys, speedstr,
                                     self.depth + 1, self.disp,
                                     self.adv_prompt(self.proffset, last)))

    def print_tree(self):
        print('%s%s' % (self.prompt, self))
        if self.children and all(child.gatherme for child in self.children):
            self.print_children_gathered()
        else:
            for child in self.children:
                child.print_tree()

    def print_children_gathered(self):
        self.children = sorted(self.children, key=lambda x: x.gathergrp())
        groups = [(group, list(children)) for group, children
                  in groupby(self.children, lambda x: x.gathergrp())]

        for index, (group, children) in enumerate(groups):
            last = bool(index == len(groups) - 1)
            prompt = self.gen_prompt(self.adv_prompt(last=last))
            speed_info = ''
            if self.disp.get('verbose') > 0:
                speeds = []
                counts = Counter(child.speedstr for child in children)
                for speed in counts:
                    if counts[speed] == 1:
                        speeds.append(speed)
                    else:
                        speeds.append('%d x %s' % (counts[speed], speed))

                speed_info = ' (%s)' % ', '.join(speeds)
            print('%s %2d x %s%s' % (prompt, len(list(children)), group,
                                     speed_info))

class SDRootNode(SDNode):
    def resolve(self):
        sas_hosts = list(self.baseobj)
        for index, obj in enumerate(sas_hosts):
            sas_host = SASHost(obj.node('device'))
            last = bool(index == len(sas_hosts) - 1)
            self.add_child(SDHostNode, sas_host, last=last)


class SDHostNode(SDNode):
    def resolve(self):

        def portsortfunc(p):
            """helper sort function to return expanders first, then order by
            scsi device type and bay identifier"""
            if len(p.expanders) > 0:
                return [1, 0, 0]
            sortv = [0, 0, 0]  # exp?, -type, bay
            try:
                if len(p.end_devices) > 0:
                    if len(p.end_devices[0].targets) > 0:
                        sortv[1] = -int(p.end_devices[0].targets[0].attrs.type)
                    sortv[2] = int(p.end_devices[0].sas_device.attrs
                                   .bay_identifier)
            except (AttributeError, IndexError, ValueError):
                pass
            return sortv

        ports = sorted(self.baseobj.ports, key=portsortfunc)
        for index, port in enumerate(ports):
            nphys = len(port.phys)
            try:
                speedstr = self._port_phys_linkrate(port)
            except AttributeError as exc:
                speedstr = 'ERROR: %s' % exc
            last = bool(index == len(self.baseobj.ports) - 1)
            for expander in port.expanders:
                self.add_child(SDExpanderNode, expander, nphys=nphys, speedstr=speedstr, last=last)
            for end_device in port.end_devices:
                self.add_child(SDEndDeviceNode, end_device, nphys=nphys, speedstr=speedstr,
                               last=last)

    def __str__(self):
        verb = self.disp.get('verbose')

        info_fmt = []
        if verb > 1:
            info_fmt += ['board: {board_name} {board_assembly} '
                         '{board_tracer}', 'product: {version_product}',
                         'bios: {version_bios}', 'fw: {version_fw}']
        elif verb > 0:
            info_fmt.append('{board_name}')
        if self.disp.get('addr'):
            info_fmt.append('addr: {host_sas_address}')

        ikeys = ('board_name', 'board_assembly', 'board_tracer',
                 'host_sas_address', 'version_product', 'version_bios',
                 'version_fw')

        # sanitize values for display
        iargs = dict((k, self.baseobj.scsi_host.attrs.get(k, 'N/A'))
                     for k in ikeys)

        return '%s %s' % (self.name, ', '.join(info_fmt).format(**iargs))

    def _port_phys_linkrate(self, port):
        """Get linkrate for all port phys as string"""
        speeds = []
        counts = Counter(phy.attrs.negotiated_linkrate for phy in port.phys)
        for speed in counts:
            if sys.stdout.isatty():
                if counts[speed] != len(port.phys):
                    fmt = "\033[91m{}\033[0m"
                else:
                    fmt = "\033[92m{}\033[0m"
            else:
                fmt = "{}"
            speeds.append(fmt.format('%d x %s' % (counts[speed], speed)))
        return ', '.join(speeds)


class SDExpanderNode(SDHostNode):
    def resolve(self):
        linkinfo = '%dx--' % self.nphys
        self.proffset = len(linkinfo)
        SDHostNode.resolve(self)

    def __str__(self):
        verb = self.disp.get('verbose')
        expander = self.baseobj

        if verb > 1:
            exp_info = ' ' + format_attrs((('vendor', 'vendor_id'),
                                     ('product', 'product_id'),
                                     ('rev', 'product_rev')),
                                    expander.attrs)
            speed_info = ' (%s)' % self.speedstr
        elif verb > 0:
            exp_info = ' ' + expander.attrs.get('vendor_id', 'N/A')
            speed_info = ' (%s)' % self.speedstr
        else:
            exp_info = ''
            speed_info = ''

        linkinfo = '%dx--' % self.nphys

        if self.disp['addr']:
            dev_info = ' ' + format_attrs((('addr', 'sas_address'),),
                                    expander.sas_device.attrs)
        else:
            dev_info = ''

        return '%s%s%s%s%s' % (linkinfo, expander.name, exp_info, dev_info, speed_info)


class SDEndDeviceNode(SDNode):
    @property
    def gatherme(self):
        return (self.disp['verbose'] < 2 and not self.disp.get('addr')
                and not self.disp.get('counters') \
                and not self.disp.get('devices')) and len(self.children) <= 1

    def gathergrp(self):
        if self.children:
            # special case: if child is an enclosure, we want to print more info
            child = self.children[0]
            undergrp = child.gathergrp()
            if undergrp == 'enclosure':
                undergrp = str(child)
        else:
            undergrp = self.name
        try:
            device_type = self.baseobj.sas_device.attrs.device_type
            device_type = device_type.replace(' ', '_')
        except AttributeError:
            device_type = 'unknown'

        return '%s -- %s' % (device_type, undergrp)

    def resolve(self):
        linkinfo = '%dx--' % self.nphys
        self.proffset = len(linkinfo)
        for index, target in enumerate(self.baseobj.targets):
            last = bool(index == len(self.baseobj.targets) - 1)
            self.add_child(SDSCSIDeviceNode, target, last=last, speedstr=self.speedstr)

    def __str__(self):
        verb = self.disp.get('verbose')
        linkinfo = '%dx--' % self.nphys
        sas_end_device = self.baseobj

        bay = None
        speed_info = ''
        if verb > 0:
            speed_info = " (%s)" % self.speedstr

        if verb > 1:
            try:
                bay = int(sas_end_device.sas_device.attrs.bay_identifier)
            except (AttributeError, ValueError):
                pass

        if bay is None:
            istr = '%s%s%s' % (linkinfo, sas_end_device.name, speed_info)
        else:
            istr = '%s%s%s bay: %d' % (linkinfo, sas_end_device.name, speed_info, bay)

        if self.disp.get('addr'):
            addr = sas_end_device.sas_device.attrs.sas_address
            istr = '%s addr: %s' % (istr, addr)

        return istr


class SDSCSIDeviceNode(SDNode):
    # Note: additional instance attribute dinfo defined in resolve()

    @property
    def gatherme(self):
        if self.disp['verbose'] >= 1 or self.disp.get('addr') or \
                self.disp.get('counters') or self.disp.get('devices'):
            return False

        # Do not gather enclosure
        try:
            return int(self.baseobj.attrs.type) != TYPE_ENCLOSURE
        except ValueError:
            return False

    def gathergrp(self):
        # gather group is our single child scsi type string
        return self.baseobj.strtype

    def resolve(self):
        verb = self.disp.get('verbose')
        self.dinfo, qinfo = self.get_scsi_device_info(self.baseobj, verb > 2)
        if qinfo:
            # spawn optional "block queue" tree leaves
            for index, (qattr, qval) in enumerate(qinfo.items()):
                last = bool(index == len(qinfo) - 1)
                self.add_child(SDBlockQueueNode, qval, name=qattr, last=last)

    def __str__(self):
        return self.dinfo  # defined in resolve()

    def get_scsi_device_info(self, scsi_device, want_queue_attrs=False):
        verb = self.disp.get('verbose')
        dev_info_fmt = []
        if verb == 1:
            dev_info_fmt.append('{vendor}')
        elif verb > 1:
            dev_info_fmt.append('vendor: {vendor}')
        if verb > 1:
            dev_info_fmt += ['model: {model}', 'rev: {rev}']
        if self.disp.get('addr'):
            dev_info_fmt.append('addr: {sas_address}')
        if self.disp.get('counters'):
            dev_info_fmt.append('IO:{{req: {iorequest_cnt}')
            dev_info_fmt.append('done: {iodone_cnt}')
            dev_info_fmt.append('error: {ioerr_cnt}}}')

        ikeys = ( 'vendor', 'model', 'rev', 'sas_address' )
        iargs = dict((k, scsi_device.attrs.get(k, 'N/A')) for k in ikeys)
        if self.disp.get('counters'):
            iokeys = ('ioerr_cnt', 'iodone_cnt', 'iorequest_cnt')
            for key in iokeys:
                iargs[key] = ast.literal_eval(scsi_device.attrs.get(key, 0))

        dev_info = ' '.join(dev_info_fmt).format(**iargs)

        dev_sg = ''
        if self.disp.get('devices'):
            sg = scsi_device.scsi_generic
            if sg:
                dev_sg = '[%s]' % sg.name

        scsi_type = scsi_device.attrs.type
        dev_type = scsi_device.strtype

        if scsi_device.block:
            block = scsi_device.block

            size = block.sizebytes()
            if size >= 1e12:
                blk_info = "size: %.1fTB" % (size / 1e12)
            else:
                blk_info = "size: %.1fGB" % (size / 1e9)

            queue_attr_info = {}

            if want_queue_attrs:
                # -vvv: print all queue attributes
                queue_attr_info = dict(scsi_device.block.queue.attrs)

            return ' '.join(
                (dev_type, dev_info, blk_info, dev_sg)), queue_attr_info
        elif dev_type == 'enclosure':
            if verb > 0:
                sg = scsi_device.scsi_generic
                snic = ses_get_snic_nickname(sg.name)
                if snic:
                    dev_type += ' %s' % snic

        return ' '.join((dev_type, dev_info, dev_sg)), {}


class SDBlockQueueNode(SDNode):
    gatherme = False

    def __str__(self):
        return 'queue.%s: %s' % (self.name, self.baseobj)


def main():
    """console_scripts entry point for sas_discover command-line."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Verbosity level, repeat multiple times!')
    parser.add_argument('--addr', action='store_true', default=False,
                        help='Print SAS addresses')
    parser.add_argument('--devices', action='store_true', default=False,
                        help='Print associated devices')
    parser.add_argument('--counters', action='store_true', default=False,
                        help='Print I/O counters')
    pargs = parser.parse_args()

    try:
        # print short hostname as tree root node
        root_name = socket.gethostname().split('.')[0]
        root_obj = sysfs.node('class').node('sas_host')
        disp = {'verbose': pargs.verbose, 'addr': pargs.addr,
                'devices': pargs.devices, 'counters': pargs.counters}
        root = SDRootNode(name=root_name, baseobj=root_obj, disp=disp)
        root.print_tree()
    except IOError:
        pass
    except KeyError as err:
        print("Not found: %s" % err, file=sys.stderr)


if __name__ == '__main__':
    main()
