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

from os.path import basename

from sasutils.scsi import ArrayDevice, BlockDevice, SCSIDevice, SCSIHost
from sasutils.sysfs import SysfsDevice


#
# SAS topology components
#

class SASPhy(SysfsDevice):

    def __init__(self, device, subsys='sas_phy'):
        SysfsDevice.__init__(self, device, subsys)


class SASPort(SysfsDevice):

    def __init__(self, device, subsys='sas_port'):
        SysfsDevice.__init__(self, device, subsys)
        self.expanders = []
        self.end_devices = []
        self.phys = []

        phys = self.device.glob('phy-*')
        for phy in phys:
            self.phys.append(SASPhy(phy))

        end_devices = self.device.glob('end_device-*')
        for end_device in end_devices:
            self.end_devices.append(SASEndDevice(end_device))

        expanders  = self.device.glob('expander-*')
        for expander in expanders:
            self.expanders.append(SASExpander(expander))

class SASNode(SysfsDevice):

    def __init__(self, device, subsys=None):
        SysfsDevice.__init__(self, device, subsys)
        self.phys = []
        self.ports = []

        ports = self.device.glob('port-*')
        for port in ports:
            #print('node has port %s' % port.path)
            self.ports.append(SASPort(port)) #port.node(port))) #'sas_port/port-*')))

        phys = self.device.glob('phy-*')
        for phy in phys:
            #print('node has phy %s' % phy.path)
            self.phys.append(SASPhy(phy)) #.node(phy))) #phy.node('sas_phy/phy-*')))

    def __repr__(self):
        return '<%s.%s %s phys=%d ports=%d>' % (self.__module__,
                                                self.__class__.__name__,
                                                self.sysfsnode.path,
                                                len(self.phys), len(self.ports))

    __str__ = __repr__

    def end_devices_by_scsi_type(self, device_type):
        """
        Iterate over end_devices (direct children) by scsi type.
        SCSI types are defined in the scsi module.
        """
        for port in self.ports:
            for end_device in port.end_devices:
                if int(end_device.scsi_device.attrs.type) == int(device_type):
                    yield end_device

class SASHost(SASNode):

    def __init__(self, device, subsys='sas_host'):
        SASNode.__init__(self, device, subsys)
        self.scsi_host = SCSIHost(device)

    def __str__(self):
        return '<%s.%s %s>' % (self.__module__, self.__class__.__name__,
                               self.__dict__)

class SASExpander(SASNode):

    def __init__(self, device, subsys='sas_expander'):
        SASNode.__init__(self, device, subsys)
        self.sas_device = SASDevice(device)

class SASDevice(SysfsDevice):

    def __init__(self, device, subsys='sas_device'):
        SysfsDevice.__init__(self, device, subsys)

class SASEndDevice(SysfsDevice):

    def __init__(self, device, subsys='sas_end_device'):
        SysfsDevice.__init__(self, device, subsys)
        self.sas_device = SASDevice(device)
        target = device.node('target*/*[0-9]')
        self.scsi_device = SCSIDevice(target)


#
# Other useful SAS classes
#

class SASBlockDevice(BlockDevice):
    """
    SAS-aware block device class that allows direct access to SASEndDevice.
    """

    def __init__(self, device):
        BlockDevice.__init__(self, device)
        self._end_device = None

    @property
    def end_device(self):
        if not self._end_device:
            self._end_device = SASEndDevice(self.sysfsnode.node('../../../..'))
        return self._end_device
