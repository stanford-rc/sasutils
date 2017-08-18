#!/usr/bin/env python
#
# Copyright (C) 2017 Board of Trustees, Leland Stanford Jr. University
#
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
import sys
import time

from sasutils.sas import SASHost
from sasutils.ses import ses_get_snic_nickname
from sasutils.scsi import MAP_TYPES
from sasutils.sysfs import sysfs


class SDNode(object):
    def __init__(self, baseobj, name=None, parent=None, prefix=''):
        self.name = name
        self.parent = parent
        self.baseobj = baseobj
        self.prefix = prefix
        self.children = []
        self.nickname = None
        self.resolve()

    def resolve(self):
        pass

    def __str__(self):
        return self.name or ''

    def bottomup(self):
        path = []
        if self.name:
            path.append(str(self))
        if isinstance(self.parent, SDNode):
            path += self.parent.bottomup()
        elif self.prefix:
            path.append(self.prefix)
        return path

    def print_counter(self, key, value):
        path = self.bottomup()
        path.reverse()
        keybase = '.'.join(path).replace(' ', '_')
        # some counters in sysfs are hex numbers
        try:
            if value.startswith('0x'):
                value = int(value, 16)
        except AttributeError:
            pass
        print('%s.%s %s %d' % (keybase, key, value, time.time()))

    def add_child(self, sdclass, parent, baseobj, name=None):
        if not name:
            baseobjname = baseobj.name  # mandatory when name not provided
        else:
            baseobjname = name
        self.children.append(sdclass(baseobj, baseobjname, parent))

    def print_tree(self):
        for child in self.children:
            child.print_tree()


class SDRootNode(SDNode):
    def resolve(self):
        for obj in self.baseobj:
            sas_host = SASHost(obj.node('device'))
            self.add_child(SDHostNode, self, sas_host)


class SDHostNode(SDNode):
    def resolve(self):

        def portsortfunc(port_n):
            """helper sort function to return expanders first, then order by
            scsi device type and bay identifier"""
            if len(port_n.expanders) > 0:
                return 1, 0, 0
            sortv = [0, 0, 0]  # exp?, -type, bay
            try:
                if len(port_n.end_devices) > 0:
                    sortv[1] = -int(port_n.end_devices[0].targets[0].attrs.type)
                    sortv[2] = int(port_n.end_devices[0].sas_device.attrs
                                   .bay_identifier)
            except (RuntimeError, ValueError):
                pass
            return sortv

        for port in sorted(self.baseobj.ports, key=portsortfunc):
            for expander in port.expanders:
                self.add_child(SDExpanderNode, self, expander)
            for end_device in port.end_devices:
                self.add_child(SDEndDeviceNode, self, end_device)

        # Phy counters
        for phy in self.baseobj.phys:
            phyid = phy.attrs.phy_identifier
            for key in ('invalid_dword_count', 'loss_of_dword_sync_count',
                        'phy_reset_problem_count',
                        'running_disparity_error_count'):
                phykey = 'phys.%s.%s' % (phyid, key)
                try:
                    self.print_counter(phykey, phy.attrs.get(key))
                except AttributeError as exc:
                    print('%s: %s' % (phy, exc), file=sys.stderr)

    def __str__(self):
        board = self.baseobj.scsi_host.attrs.get('board_name', 'UNKNOWN_BOARD')
        addr = self.baseobj.scsi_host.attrs['host_sas_address']
        return '.'.join((board, addr))


class SDExpanderNode(SDHostNode):
    def __str__(self):
        expander = self.baseobj
        if self.nickname:
            nick = self.nickname
        else:
            nick = 'expander_%s' % expander.sas_device.attrs['sas_address']
        return '.'.join((expander.attrs.get('product_id', 'UNKNOWN'), nick))


class SDEndDeviceNode(SDNode):
    def resolve(self):
        for target in self.baseobj.targets:
            self.add_child(SDSCSIDeviceNode, self, target)

    def __str__(self):
        sas_end_device = self.baseobj

        bay = None
        try:
            bay = int(sas_end_device.sas_device.attrs.bay_identifier)
        except (AttributeError, ValueError):
            pass

        if bay is None:
            return 'no-bay.%s' % sas_end_device.name

        return 'bays.%s' % bay


class SDSCSIDeviceNode(SDNode):
    def resolve(self):
        # Display device errors (work with both ses and sd drivers)
        scsi_device = self.baseobj
        self.print_counter('ioerr_cnt', scsi_device.attrs['ioerr_cnt'])
        self.print_counter('iodone_cnt', scsi_device.attrs['iodone_cnt'])
        self.print_counter('iorequest_cnt', scsi_device.attrs['iorequest_cnt'])

    def __str__(self):
        return self.get_scsi_device_info(self.baseobj)

    def get_scsi_device_info(self, scsi_device):
        # print(scsi_device.sysfsnode.path)
        dev_info = '.'.join((scsi_device.attrs.get('model', 'MODEL_UNKNOWN'),
                             scsi_device.attrs['sas_address']))

        scsi_type = scsi_device.attrs.type
        unknown_type = 'unknown[%s]' % scsi_type
        try:
            dev_type = MAP_TYPES.get(int(scsi_type), unknown_type)
        except ValueError:
            dev_type = 'unknown scsi type'

        if dev_type == 'enclosure':
            sg = scsi_device.scsi_generic
            snic = ses_get_snic_nickname(sg.name)
            # automatically resolve parent expander nickname
            self.parent.parent.nickname = snic
            if snic:
                return '.'.join((scsi_device.attrs.get('model',
                                                       'MODEL_UNKNOWN'), snic))

        return dev_info


def main():
    """console_scripts entry point for sas_counters command-line."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', action='store',
                        default='sasutils.sas_counters',
                        help='carbon prefix (example: "datacenter.cluster",'
                             ' default is "sasutils.sas_counters")')
    pargs = parser.parse_args()
    pfx = pargs.prefix.strip('.')
    try:
        # print short hostname as tree root node
        root_name = socket.gethostname().split('.')[0]
        root_obj = sysfs.node('class').node('sas_host')
        SDRootNode(root_obj, name=root_name, prefix=pfx).print_tree()
    except IOError:
        pass
    except KeyError as err:
        print("Not found: %s" % err, file=sys.stderr)


if __name__ == '__main__':
    main()
