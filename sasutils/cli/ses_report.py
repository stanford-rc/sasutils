#!/usr/bin/env python
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


"""
ses_report - SES status and metrics reporting utility
"""

from __future__ import print_function
import argparse
import json
import logging
import time
import sys

from sasutils.scsi import EnclosureDevice
from sasutils.ses import ses_get_ed_metrics, ses_get_ed_status
from sasutils.ses import ses_get_snic_nickname
from sasutils.sysfs import sysfs


def _init_argparser():
    """Initialize argparser object for ses_report command-line."""
    desc = 'SES status and metrics reporting utility (part of sasutils).'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-d', '--debug', action="store_true",
                        help='enable debugging')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--carbon', action='store_true',
                       help='output SES Element descriptors metrics in a '
                            'format suitable for Carbon/Graphite')
    group.add_argument('-s', '--status', action='store_true',
                       help='output status found in SES Element descriptors')

    group = parser.add_argument_group('output options')
    group.add_argument('--prefix', action='store',
                       default='sasutils.ses_report',
                       help='carbon prefix (example: "datacenter.cluster",'
                            ' default is "sasutils.ses_report")')
    group.add_argument('-j', '--json', action='store_true',
                       help='alternative JSON output mode')
    return parser.parse_args()


def ses_report():
    """ses_report command-line"""
    pargs = _init_argparser()
    if pargs.debug:
        # debugging on the same stream is recommended (stdout)
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    pfx = pargs.prefix.strip('.')
    if pfx:
        pfx += '.'

    json_encl_dict = {}

    # Iterate over sysfs SCSI enclosures
    for node in sysfs.node('class').node('enclosure'):
        # Get enclosure device
        enclosure = EnclosureDevice(node.node('device'))
        # Get enclosure SG device
        sg_dev = enclosure.scsi_generic
        # Resolve SES enclosure nickname
        snic = ses_get_snic_nickname(sg_dev.name)
        if snic:
            snic = snic.replace(' ', '_')
        else:
            # Use Vendor + SAS address if SES encl. nickname not defined
            snic = enclosure.attrs.vendor.replace(' ', '-')
            snic += '_' + enclosure.attrs.sas_address

        if pargs.carbon:
            if pargs.json:
                encl_json_list = []
                for edinfo in ses_get_ed_metrics(sg_dev.name):
                    encl_json_list.append(edinfo)
                json_encl_dict[snic] = encl_json_list
            else:
                time_now = time.time()
                for edinfo in ses_get_ed_metrics(sg_dev.name):
                    # Print output using Carbon format
                    fmt = '{element_type}.{descriptor}.{key}_{unit} {value}'
                    path = fmt.format(**edinfo)
                    print('%s%s.%s %d' % (pfx, snic, path, time_now))
        else:
            if pargs.json:
                encl_json_list = []
                for edstatus in ses_get_ed_status(sg_dev.name):
                    encl_json_list.append(edstatus)
                json_encl_dict[snic] = encl_json_list
            else:
                for edstatus in ses_get_ed_status(sg_dev.name):
                    fmt = '{element_type}.{descriptor} {status}'
                    output = fmt.format(**edstatus)
                    print('%s%s.%s' % (pfx, snic, output))

    if pargs.json:
        print(json.dumps(json_encl_dict, sort_keys=True, indent=4))


def main():
    """console_scripts entry point for ses_report"""
    try:
        ses_report()
    except KeyError as err:
        print("Not found: {0}".format(err), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
