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


import collections
import json
import glob
from os import access, listdir, readlink, R_OK
from os.path import basename, isdir, isfile, join, realpath
import string


SYSFS_ROOT = '/sys'


class SysfsNode(object):

    def __init__(self, path=None):
        if path is None:
            self.path = SYSFS_ROOT
        else:
            self.path = path

    def __repr__(self):
        return '<sysfs.SysfsNode "%s">' % self.path

    def __str__(self):
        return basename(self.path)

    def __eq__(self, other):
        return realpath(self.path) == realpath(other.path)

    def __hash__(self):
        return hash(realpath(self.path))

    def __iter__(self):
        return iter(self.__class__(join(self.path, name))
                    for name in listdir(self.path))

    def iterglob(self, pathname, is_dir=True):
        for path in glob.glob(join(self.path, pathname)):
            if isfile(path):
                yield basename(path)
            elif is_dir and isdir(path):
                yield self.__class__(path)

    def glob(self, pathname, is_dir=True):
        return list(self.iterglob(pathname, is_dir))

    def node(self, pathname, default=None):
        glob_res = list(self.iterglob(pathname))
        try:
            return glob_res[0]
        except IndexError:
            if default is not None:
                return default
            # print meaningfull error
            raise KeyError(join(self.path, pathname))

    def iterget(self, pathname, ignore_errors, absolute=False):
        if absolute:
            path = pathname
        else:
            path = join(self.path, pathname)
        for path in glob.glob(path):
            if isfile(path) and access(path, R_OK):
                try:
                    with open(path, 'r') as fp:
                        yield fp.read().strip()
                except IOError, exc:
                    if not ignore_errors:
                        yield str(exc)

    def get(self, pathname, default=None, ignore_errors=False, printable=True,
            absolute=False):
        if absolute:
            path = pathname
        else:
            path = join(self.path, pathname)
        glob_res = list(self.iterget(path, ignore_errors, absolute=True))
        try:
            result = glob_res[0]
        except IndexError:
            if not ignore_errors:
                raise KeyError('Not found: %s' % path)
            result = default

        if not result:
            return result
        #elif printable and all(c in string.printable for c in result):
        else:
            return result
        #else:
        #    return default

    def readlink(self, pathname, default=None, absolute=False):
        if absolute:
            path = pathname
        else:
            path = join(self.path, pathname)
        try:
            return readlink(path)
        except OSError:
            if default is not None:
                return default
            raise


# For testing
SYSFSNODE_CLASS = SysfsNode

sysfs = SYSFSNODE_CLASS()


class SysfsAttributes(collections.MutableMapping):
    """SysfsObject attributes with dot.notation access"""

    def __init__(self):
        self.values = {}
        self.paths = {}

    def add_path(self, attr, path):
        self.paths[attr] = path

    def load(self):
        for path in self.paths:
            loaded = self[path]

    # The next five methods are requirements of the ABC.

    def __setitem__(self, key, value):
        self.values[key] = value

    def __getitem__(self, key):
        if not self.values.__contains__(key):
            try:
                self.values[key] = SYSFSNODE_CLASS().get(self.paths[key],
                                                         absolute=True)
            except KeyError:
                raise AttributeError("%r object has no attribute %r" %
                                     (self.__class__.__name__, key))
        return self.values[key]

    def __delitem__(self, key):
        if key in self.values:
            del self.values[key]
        del self.paths[key]

    def __iter__(self):
        return iter(self.paths)

    def __len__(self):
        return len(self.paths)

    __getattr__ = __getitem__


class SysfsObject(object):

    def __init__(self, sysfsnode):
        self.sysfsnode = sysfsnode
        self.name = str(sysfsnode)
        self.attrs = SysfsAttributes()
        self.classname = self.__class__.__name__
        if type(sysfsnode) is str:
            assert len(sysfsnode) > 0
        attrs = self.sysfsnode.glob('*', is_dir=False)
        for attr in attrs:
            self.attrs.add_path(attr, join(self.sysfsnode.path, attr))

    def json_serialize(self):
        """May be overridden to change json serialization, eg. to avoid
        circular reference issues."""
        return self.__dict__

    def to_json(self):

        def json_default(o):
            if hasattr(o, 'json_serialize'):
                return o.json_serialize()
            return o.__dict__

        return json.dumps(self, default=json_default, sort_keys=True, indent=4)

    def __eq__(self, other):
        return self.sysfsnode == other.sysfsnode

    def __hash__(self):
        return hash(self.sysfsnode)

    def __repr__(self):
        return '<%s.%s %r>' % (self.__module__, self.__class__.__name__,
                               self.sysfsnode.path)

    __str__ = __repr__


class SysfsDevice(SysfsObject):

    def __init__(self, device, subsys, sysfsdev_pattern='*[0-9]'):
        # only consider end_device-20:2:57, 20:0:119:0, host19
        SysfsObject.__init__(self, device.node('%s/%s' % (subsys,
                                                          sysfsdev_pattern)))
        self.device = device
