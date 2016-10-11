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


from __future__ import print_function
import argparse
import socket

from sasutils.sas import SASHost
from sasutils.ses import ses_get_snic_nickname
from sasutils.scsi import TYPE_MAP
from sasutils.sysfs import sysfs

#
# Helpers for text-based representation of the tree topology
#

def gen_prompt(prinfo):
    prompt = []
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

def adv_prompt(prinfo, offset=0, last=False):
    if last:
        plink = '`'
    else:
        plink = '|'
    return prinfo + [(plink, offset)]

def format_attrs(attrlist, attrs):
    """filter keys to avoid SysfsObject cache miss on all attrs"""
    attr_fmt = ('%s: {%s}' % t for t in attrlist)
    iargs = dict((k, attrs[k]) for _, k in attrlist)
    return ', '.join(attr_fmt).format(**iargs)


#
# Main class for sas_discover
#

class SASDiscoverCLI(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--verbose', '-v', action='count', default=0,
                            help='Verbosity level, repeat multiple times!')
        parser.add_argument('--addr', action='store_true', default=False,
                            help='Print SAS addresses')
        self.args = parser.parse_args()

    def print_hosts(self, sysfsnode, prinfo):
        prompt = gen_prompt(prinfo)
        num_hosts = len(list(sysfsnode))
        for index, sas_host in enumerate(sysfsnode):
            if index == num_hosts - 1:
                prinfo = adv_prompt([], last=True)
                prompt = gen_prompt(prinfo)

            sas_host = SASHost(sas_host.node('device'))

            info_fmt = []
            if self.args.verbose > 1:
                info_fmt += ['board: {board_name} {board_assembly} '
                             '{board_tracer}', 'product: {version_product}',
                             'bios: {version_bios}', 'fw: {version_fw}']
            elif self.args.verbose > 0:
                info_fmt.append('{board_name}')
            if self.args.addr:
                info_fmt.append('addr: {host_sas_address}')

            ikeys = ('board_name', 'board_assembly', 'board_tracer',
                     'host_sas_address', 'version_product', 'version_bios',
                     'version_fw')

            iargs = dict((k, sas_host.scsi_host.attrs[k]) for k in ikeys)

            print('%s%s %s' % (prompt, sas_host.name,
                               ', '.join(info_fmt).format(**iargs)))

            num_ports = len(sas_host.ports)
            for index, port in enumerate(sas_host.ports):
                if index == num_ports - 1:
                    self.print_expanders(port, adv_prompt(prinfo, last=True))
                else:
                    self.print_expanders(port, adv_prompt(prinfo))

    def print_expanders(self, port, prinfo):
        prompt = gen_prompt(prinfo)
        for expander in port.expanders:
            if self.args.verbose > 1:
                exp_info = format_attrs((('vendor', 'vendor_id'),
                                         ('product', 'product_id'),
                                         ('rev', 'product_rev')),
                                        expander.attrs)
            elif self.args.verbose > 0:
                exp_info = expander.attrs['vendor_id']
            else:
                exp_info = ''

            linkinfo = '-%dx--' % len(port.phys)

            dev_info = ''

            if self.args.addr:
                dev_info = format_attrs((('addr', 'sas_address'),),
                                        expander.sas_device.attrs)
            print('%s%s%s %s %s' % (prompt, linkinfo, expander.name,
                                    exp_info, dev_info))

            exp_blkdevs = []

            poff = len(linkinfo)
            num_ports = len(expander.ports)
            for index, port in enumerate(expander.ports):
                if index == num_ports - 1 and not exp_blkdevs:
                    self.print_expanders(port, adv_prompt(prinfo, poff, True))
                    blkdevs = self.print_devices(port, adv_prompt(prinfo, poff, True))
                else:
                    self.print_expanders(port, adv_prompt(prinfo, poff))
                    blkdevs = self.print_devices(port, adv_prompt(prinfo, poff))
                exp_blkdevs += blkdevs
            if exp_blkdevs:
                prompt = gen_prompt(adv_prompt(prinfo, poff, True))
                print('%s %d block devices (use -vv for details)'
                      % (prompt, len(exp_blkdevs)))

    def print_devices(self, port, prinfo):
        prompt = gen_prompt(prinfo)
        linkinfo = '-%dx--' % len(port.phys)

        if len(port.end_devices) > 1:
            print('warning len(port.end_devices) == %d' % len(port.end_devices))

        blkdevs = []

        for end_device in port.end_devices:
            dev_info_fmt = []
            if self.args.verbose == 1:
                dev_info_fmt.append('{vendor}')
            elif self.args.verbose > 1:
                dev_info_fmt.append('vendor: {vendor}')
            if self.args.verbose > 1:
                dev_info_fmt += ['model: {model}', 'rev: {rev}']
            if self.args.addr:
                dev_info_fmt.append('addr: {sas_address}')

            ikeys = ('vendor', 'model', 'rev', 'sas_address')
            iargs = dict((k, end_device.scsi_device.attrs[k]) for k in ikeys)
            dev_info = ', '.join(dev_info_fmt).format(**iargs)

            unknown_type = 'unknown(%s)' % end_device.scsi_device.attrs.type
            dev_type = TYPE_MAP.get(int(end_device.scsi_device.attrs.type),
                                    unknown_type)

            if end_device.scsi_device.block:
                block = end_device.scsi_device.block

                if self.args.verbose < 2:
                    blkdevs.append(block)
                    continue

                size = block.sizebytes()
                if size >= 1e12:
                    blk_info = "size %.1fTB" % (size / 1e12)
                else:
                    blk_info = "size %.1fGB" % (size / 1e9)
                #print(dict(end_device.scsi_device.block.queue.attrs))
                print('%s%s%s %s %s %s' % (prompt, linkinfo, end_device.name,
                                           dev_type, dev_info, blk_info))
            else:
                sg = end_device.scsi_device.scsi_generic
                snic = ses_get_snic_nickname(sg.name)
                if snic:
                    dev_type += ' %s' % snic
                print('%s%s%s %s %s' % (prompt, linkinfo, end_device.name,
                                        dev_type, dev_info))

        return blkdevs

def main():
    """console_scripts entry point for sas_discover command-line."""
    # print short hostname as tree root node
    print(socket.gethostname().split('.')[0])

    # start from /sys/class/sas_host
    root = sysfs.node('class').node('sas_host')
    SASDiscoverCLI().print_hosts(root, adv_prompt([]))

if __name__ == '__main__':
    main()
