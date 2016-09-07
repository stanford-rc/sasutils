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

import glob
import nose
import os
from os.path import basename, dirname, isdir, isfile, islink, join
import sys

# use zipfile as it is safer than tarfile with sysfs
# see http://bugs.python.org/issue10760
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import sasutils.sysfs
from sasutils.cli.sas_discover import SASDiscoverCLI, adv_prompt
from sasutils.sas import SASHost


def zipfile_add(path):
    try:
        #print(path, file=sys.stderr)
        zipfile.write(path)
    except OSError as err:
        print('zipfile OSError %s for %s' % (err, path), file=sys.stderr)


class SysfsNodeDump(sasutils.sysfs.SysfsNode):

    def __iter__(self):
        for name in os.listdir(self.path):
            path = join(self.path, name)
            zipfile_add(path)
            yield self.__class__(path)

    def iterglob(self, pathname, is_dir=True):
        for path in glob.glob(join(self.path, pathname)):
            if isfile(path):
                zipfile_add(path)
            elif is_dir and isdir(path):
                zipfile_add(path)
        return super(SysfsNodeDump, self).iterglob(pathname, is_dir)

    def get(self, pathname, default=None, ignore_errors=False, printable=True,
            absolute=False):
        if absolute:
            path = pathname
        else:
            path = join(self.path, pathname)
        zipfile.write(path)
        return super(SysfsNodeDump, self).get(pathname, default, ignore_errors,
                                              printable)

    def readlink(self, pathname, default=None, absolute=False):
        if absolute:
            path = pathname
        else:
            path = join(self.path, pathname)
        print(path)
        zipfile_add(path)
        return super(SysfsNodeDump, self).readlink(pathname, default)


sasutils.sysfs.SYSFSNODE_CLASS = SysfsNodeDump
sysfs = sasutils.sysfs.sysfs = SysfsNodeDump()


if __name__ == '__main__':
    zipfile = ZipFile('sysfs_testenv.zip', 'w')
    os.environ['gen_sysfs_testenv'] = 'TRUE'
    nose.run(argv=[sys.argv[0], 'sysfs', '-v'])
    zipfile.close()
