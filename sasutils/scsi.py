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


from sasutils.sysfs import SysfsDevice, SysfsObject

#
# SCSI classes
#

class SCSIHost(SysfsDevice):

    def __init__(self, device, subsys='scsi_host'):
        SysfsDevice.__init__(self, device, subsys)


class SCSIDisk(SysfsDevice):

    def __init__(self, device, subsys='scsi_disk'):
        SysfsDevice.__init__(self, device, subsys)

class SCSIGeneric(SysfsDevice):

    def __init__(self, device, subsys='scsi_generic'):
        SysfsDevice.__init__(self, device, subsys)
        # the basename of self.sysfsnode is the name of the sg device
        self.sg_devname = str(self.sysfsnode)

class SCSIDevice(SysfsObject):

    def __init__(self, device):
        # scsi_device attrs attached to device
        SysfsObject.__init__(self, device)
        self.scsi_generic = SCSIGeneric(self.sysfsnode)
        try:
            self.scsi_disk = SCSIDisk(self.sysfsnode)
        except KeyError:
            pass
        try:
            self.block = BlockDevice(self.sysfsnode, scsi_device=self)
        except KeyError:
            pass

#
# SCSI bus classes
#

class EnclosureDevice(SCSIDevice):
    """Managed enclosure device"""

    def __init__(self, device):
        SCSIDevice.__init__(self, device)

class ArrayDevice(SysfsObject):

    def __init__(self, sysfsnode):
        SysfsObject.__init__(self, sysfsnode)
        self.enclosure = EnclosureDevice(sysfsnode.node('../device'))

#
# Block devices
#

class BlockDevice(SysfsDevice):
    """
    SASBlockDevice -> array_device (ArrayDevice) -> enclosure (EnclosureDevice)
    """

    def __init__(self, device, subsys='block', scsi_device=None):
        SysfsDevice.__init__(self, device, subsys, sysfsdev_pattern='sd*')
        self._scsi_device = scsi_device
        self.queue = SysfsObject(self.sysfsnode.node('queue'))
        self._array_device = None

    def json_serialize(self):
        data = dict(self.__dict__)
        if self._scsi_device is not None:
            data['_scsi_device'] = repr(self._scsi_device)
        return data

    @property
    def array_device(self):
        if not self._array_device:
            try:
                array_node = self.device.node('enclosure_device:*')
                self._array_device = ArrayDevice(array_node)
            except KeyError:
                # no enclosure_device, this may happen due to sysfs issues
                pass
        return self._array_device

    @property
    def scsi_device(self):
        if not self._scsi_device:
            self._scsi_device = SCSIDevice(self.device)
        return self._scsi_device
