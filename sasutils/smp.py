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

"""SMP Link Layer utils

Use SMPDiscover to perform a SAS topology discovery for a specified expander
using SMP and retrieve results for each phy.

Requires smp_utils.


    >>> from sasutils.smp import SMPDiscover
    >>> print SMPDiscover('/dev/bsg/expander-16:0')
    phy:0 negot:U addr:0x500605b00aaf8c30 rphy:3 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:1 negot:U addr:0x500605b00aaf8c30 rphy:2 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:2 negot:U addr:0x500605b00aaf8c30 rphy:1 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:3 negot:U addr:0x500605b00aaf8c30 rphy:0 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:12 negot:U addr:0x5001636001a42e3f rphy:13 devtype:exp iproto:None tproto:SMP speed:12
    phy:13 negot:U addr:0x5001636001a42e3f rphy:12 devtype:exp iproto:None tproto:SMP speed:12
    phy:14 negot:U addr:0x5001636001a42e3f rphy:14 devtype:exp iproto:None tproto:SMP speed:12
    phy:15 negot:U addr:0x5001636001a42e3f rphy:15 devtype:exp iproto:None tproto:SMP speed:12
    phy:28 negot:U addr:0x500605b00aaf8c30 rphy:7 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:29 negot:U addr:0x500605b00aaf8c30 rphy:6 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:30 negot:U addr:0x500605b00aaf8c30 rphy:5 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:31 negot:U addr:0x500605b00aaf8c30 rphy:4 devtype:i iproto:SSP+STP+SMP tproto:None speed:12
    phy:48 negot:D addr:0x50012be000083c7d rphy:0 devtype:V iproto:SMP tproto:SSP speed:12
"""

__author__ = 'sthiell@stanford.edu (Stephane Thiell)'

import re
from subprocess import check_output
from sysfs import SysfsObject


class PhyBaseDesc(object):
    """SAS Phy description (disabled)."""

    def __init__(self, phy, routing, negot):
        """Constructor for PhyBaseDesc."""
        self.phy = int(phy)
        self.routing = routing
        self.negot = negot

    def __lt__(self, other):
        return self.phy < other.phy

    def __repr__(self):
        return '<%s.%s "%d">' % (self.__module__, self.__class__.__name__,
                                 self.phy)

    def __str__(self):
        return 'phy:{phy} routing:{routing} negot:{negot}'.format(**self.__dict__)


class PhyDesc(PhyBaseDesc):
    """SAS Phy description."""

    def __init__(self, phy, routing, addr, rphy, devtype, iproto, tproto, speed):
        """Constructor for PhyDesc.

        Args:
          phy: phy index
          routing: routing attribute
          addr: SAS addr of phy#
          rphy: relative/remote phy#
          devtype: exp (expander) or V (virtual) or 'phy' (physical)
          iproto: initiator link protos
          tproto: target link protos
          speed: link speed
        """
        PhyBaseDesc.__init__(self, phy, routing, 'attached')
        self.rphy = int(rphy)
        self.addr = addr if addr.startswith('0x') else '0x' + addr
        self.devtype = devtype or 'phy'
        self.iproto = iproto
        self.tproto = tproto
        self.speed = speed

    def __str__(self):
        return 'phy:{phy} routing:{routing} addr:{addr} rphy:{rphy} ' \
               'devtype:{devtype} iproto:{iproto} tproto:{tproto} ' \
               'speed:{speed}'.format(**self.__dict__)


class SMPDiscover(object):
    """Performs SMP DISCOVER and gathers results."""

    def __init__(self, bsg):
        """Constructor for SMPDiscover."""
        if isinstance(bsg, SysfsObject):
            bsg = bsg.name
        self.bsg = bsg if bsg.startswith('/') else '/dev/bsg/' + bsg
        self._attached_phys = {}
        self._detached_phys = {}

        output = check_output(('smp_discover', self.bsg))

        # phy  12:U:attached:[5001636001a42e3f:13 exp t(SMP)]  12 Gbps
        # phy  28:U:attached:[500605b00ab06f40:07  i(SSP+STP+SMP)]  12 Gbps
        # phy  48:D:attached:[50012be000083c7d:00  V i(SMP) t(SSP)]  12 Gbps
        pattern = r'^\s*phy\s+(\d+):([A-Z]):attached:\[(\w+):(\d+)\s+(?:(\w+)\s+)*' \
                  r'[i]*(?:\(([a-zA-Z+]+)\))*\s*[t]*(?:\(([a-zA-Z+]+)\))*\]' \
                  r'\s+(\d+)\s+Gbps'

        for mobj in re.finditer(pattern, output, flags=re.MULTILINE):
            self._attached_phys[int(mobj.group(1))] = PhyDesc(*mobj.groups())

        # other detached phys
        pattern = r'^\s*phy\s+(\d+):([A-Z]):([\w\s]+)$'

        for mobj in re.finditer(pattern, output, flags=re.MULTILINE):
            self._detached_phys[int(mobj.group(1))] = PhyBaseDesc(*mobj.groups())


    def __repr__(self):
        return '<%s.%s "%s">' % (self.__module__, self.__class__.__name__,
                                 self.bsg)

    def __str__(self):
        return '\n'.join(str(phydesc) for phydesc in self)

    def __iter__(self):
        """Iterates through each phy description."""
        return iter(sorted(self._attached_phys.values()))

    def iterdetached(self):
        """Iterates through each detached phy description."""
        return iter(sorted(self._detached_phys.values()))
