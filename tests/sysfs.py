
import os
from os.path import dirname, join
import sys
from unittest import TestCase

import sasutils.sysfs
from sasutils.sysfs import SysfsNode, SysfsObject, SysfsDevice

if 'gen_sysfs_testenv' not in os.environ:
    sasutils.sysfs.SYSFS_ROOT = 'sys'

sysfsroot = sasutils.sysfs.SYSFS_ROOT

sysfs = sasutils.sysfs.SYSFSNODE_CLASS()


class SysfsNodeTest(TestCase):
    """Test cases for SysfsNode"""

    def setUp(self):
        self.sd = str(sysfs.node('block').glob('sd*')[0])

    def test_default(self):
        self.assertEqual(sysfs.path, sysfsroot)
        self.assertEqual(str(sysfs), 'sys')

    def test_iter(self):
        block = sysfs.node('block')
        for i in block:
            self.assertTrue(isinstance(i, SysfsNode) or isinstance(i) is basestring)

    def test_glob(self):
        block = sysfs.node('block')
        self.assertEqual(block.path, join(sysfsroot, 'block'))
        sdlist = block.glob('sd*')
        self.assertTrue(isinstance(sdlist[0], SysfsNode))
        self.assertEqual(dirname(sdlist[0].path), join(sysfsroot, 'block'))

    """
    def test_readlink(self):
        blkdevnode = sysfs.node('block').node(self.sd)
        self.assertTrue(blkdevnode.readlink('device').startswith('../'))
        self.assertRaises(OSError, sysfs.node('block').readlink, 'dummyentry')
    """

    def test_globfile(self):
        blkdevnode = sysfs.node('block').node(self.sd)
        self.assertTrue(blkdevnode.glob('remov*')[0], 'removable')

    def test_node(self):
        blkdevnode = sysfs.node('block').node(self.sd)
        self.assertRaises(KeyError, blkdevnode.node, 'dummyentry')
        self.assertEqual(blkdevnode.node('dummyentry', default='foo'), 'foo')

    def test_get(self):
        blkdevnode = sysfs.node('block').node(self.sd)
        self.assertIn(blkdevnode.get('removable'), ('0', '1'))
        self.assertRaises(KeyError, blkdevnode.get, 'dummyentry')
        self.assertEqual(blkdevnode.get('dummyentry', ignore_errors=True), None)


class SysfsObjectTest(TestCase):
    """Test cases for SysfsObject"""

    def setUp(self):
        self.sd = str(sysfs.node('block').glob('sd*')[0])

    def test_create(self):
        sysfsobj = SysfsObject(sysfs.node('block').node(self.sd))
        self.assertEqual(sysfsobj.sysfsnode.path, join(sysfsroot, 'block/%s' % self.sd))
        self.assertTrue(sysfsobj.attrs.size > 0)


class SysfsDeviceTest(TestCase):
    """Test cases for SysfsDevice"""

    def setUp(self):
        self.sd = str(sysfs.node('block').glob('sd*')[0])

    def test_create(self):
        dev = sysfs.node('block').node(self.sd).node('device')
        sysfsdev = SysfsDevice(dev, subsys='block', sysfsdev_pattern='sd*')
        self.assertEqual(sysfsdev.device.path,
                         join(sysfsroot, 'block/%s/device' % self.sd))
        self.assertEqual(sysfsdev.sysfsnode.path,
                         join(sysfsroot, 'block/%s/device/block/%s' % (self.sd, self.sd)))
