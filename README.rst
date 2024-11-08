sasutils is a set of command-line tools and a Python library to ease the administration of Serial Attached SCSI (SAS) storage networks.

.. image:: https://img.shields.io/pypi/v/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/

.. image:: https://img.shields.io/pypi/pyversions/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/
    :alt: Supported Python Versions

.. image:: https://img.shields.io/pypi/l/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/
    :alt: License

sasutils command-line tools
===========================

* sas_counters
* sas_devices
* sas_discover
* ses_report

Also, a few "zeroconf" udev scripts for use in udev rules that create friendly device aliases using SES-2 subenclosure nicknames.

* sas_mpath_snic_alias
* sas_sd_snic_alias
* sas_st_snic_alias

.. note::

       While **sasutils** gets most of the system data from sysfs (/sys), `sg_ses` (available in sg3_utils or sg3-utils)
       and `smp_discover` (available in smp_utils or smp-utils) are required for some SES features to work.

.. warning::

       **sasutils** is known to be broken with the new SAS 24Gb/s Broadcom driver mpi3mr. This driver is currently not
       creating sas objects (sas_host, etc.) in sysfs, which are used by sasutils. Suggestions are welcome.


sas_counters
------------

**sas_counters** reports SAS/SES/SD I/O and phy error counters and provides SAS topology information in an output suitable for Carbon/Graphite.
This command also supports SES-2 nicknames as seen in the example below (``io1-sassw1`` is the nickname of a SAS switch and ``io1-jbod1-0`` is the nickname of a JBOD SIM).

    .. code-block::

        $ sas_counters
        ...
        oak-io1-s1.SAS9300-8e.0x500605b00ab01234.Switch184.io1-sassw1.JB4602_SIM_0.io1-jbod1-0.bays.41.ST8000NM0075.0x5000c50084c79876.ioerr_cnt 2 1487457378
        oak-io1-s1.SAS9300-8e.0x500605b00ab01234.Switch184.io1-sassw1.JB4602_SIM_0.io1-jbod1-0.bays.41.ST8000NM0075.0x5000c50084c79876.iodone_cnt 7154904 1487457378
        oak-io1-s1.SAS9300-8e.0x500605b00ab01234.Switch184.io1-sassw1.JB4602_SIM_0.io1-jbod1-0.bays.41.ST8000NM0075.0x5000c50084c79876.iorequest_cnt 7154906 1487457378
        ...
        oak-io1-s1.SAS9300-8e.0x500605b00ab05678.Switch184.io1-sassw2.phys.15.invalid_dword_count 5 1487457378
        oak-io1-s1.SAS9300-8e.0x500605b00ab05678.Switch184.io1-sassw2.phys.15.loss_of_dword_sync_count 1 1487457378
        oak-io1-s1.SAS9300-8e.0x500605b00ab05678.Switch184.io1-sassw2.phys.15.phy_reset_problem_count 0 1487457378
        oak-io1-s1.SAS9300-8e.0x500605b00ab05678.Switch184.io1-sassw2.phys.15.running_disparity_error_count 1 1487457378
        ...


sas_discover
------------

Display SAS topology. By default, **sas_discover** tries to fold common devices (like disks). Use ``-v``, ``-vv`` or ``-vvv`` and ``--addr`` to display more details.
Below is an example with a large topology with multiple SAS HBAs, SAS switches and SAS JBODs.

    .. code-block::

        $ sas_discover -v
        oak-io8-s2
        |--host1 HBA 9500-16e
        |  `--8x--expander-1:0 ASTEK 
        |         |--1x--end_device-1:0:0
        |         |      `--enclosure io8-sassw2 ASTEK 
        |         |--4x--expander-1:1 HGST 
        |         |      |--1x--end_device-1:1:0
        |         |      |      `--enclosure io8-jbod1 HGST 
        |         |      |--10x--expander-1:9 HGST 
        |         |      |  `-- 50 x end_device -- disk
        |         |      `--10x--expander-1:10 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:2 HGST 
        |         |      |--1x--end_device-1:2:0
        |         |      |      `--enclosure io8-jbod2 HGST 
        |         |      |--10x--expander-1:11 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:12 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:3 HGST 
        |         |      |--1x--end_device-1:3:0
        |         |      |      `--enclosure io8-jbod3 HGST 
        |         |      |--10x--expander-1:13 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:14 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:4 HGST 
        |         |      |--1x--end_device-1:4:0
        |         |      |      `--enclosure io8-jbod4 HGST 
        |         |      |--10x--expander-1:15 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:16 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:5 HGST 
        |         |      |--1x--end_device-1:5:0
        |         |      |      `--enclosure io8-jbod5 HGST 
        |         |      |--10x--expander-1:17 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:18 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:6 HGST 
        |         |      |--1x--end_device-1:6:0
        |         |      |      `--enclosure io8-jbod6 HGST 
        |         |      |--10x--expander-1:19 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:20 HGST 
        |         |         `-- 51 x end_device -- disk
        |         |--4x--expander-1:7 HGST 
        |         |      |--1x--end_device-1:7:0
        |         |      |      `--enclosure io8-jbod7 HGST 
        |         |      |--10x--expander-1:21 HGST 
        |         |      |  `-- 51 x end_device -- disk
        |         |      `--10x--expander-1:22 HGST 
        |         |         `-- 51 x end_device -- disk
        |         `--4x--expander-1:8 HGST 
        |                |--1x--end_device-1:8:0
        |                |      `--enclosure io8-jbod8 HGST 
        |                |--10x--expander-1:23 HGST 
        |                |  `-- 51 x end_device -- disk
        |                `--10x--expander-1:24 HGST 
        |                   `-- 51 x end_device -- disk
        `--host10 HBA 9500-16e
           `--8x--expander-10:0 ASTEK 
                  |--1x--end_device-10:0:0
                  |      `--enclosure io8-sassw1 ASTEK 
                  |--4x--expander-10:1 HGST 
                  |      |--1x--end_device-10:1:0
                  |      |      `--enclosure io8-jbod1 HGST 
                  |      |--10x--expander-10:9 HGST 
                  |      |  `-- 50 x end_device -- disk
                  |      `--10x--expander-10:10 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:2 HGST 
                  |      |--1x--end_device-10:2:0
                  |      |      `--enclosure io8-jbod2 HGST 
                  |      |--10x--expander-10:11 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:12 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:3 HGST 
                  |      |--1x--end_device-10:3:0
                  |      |      `--enclosure io8-jbod3 HGST 
                  |      |--10x--expander-10:13 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:14 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:4 HGST 
                  |      |--1x--end_device-10:4:0
                  |      |      `--enclosure io8-jbod4 HGST 
                  |      |--10x--expander-10:15 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:16 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:5 HGST 
                  |      |--1x--end_device-10:5:0
                  |      |      `--enclosure io8-jbod5 HGST 
                  |      |--10x--expander-10:17 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:18 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:6 HGST 
                  |      |--1x--end_device-10:6:0
                  |      |      `--enclosure io8-jbod6 HGST 
                  |      |--10x--expander-10:19 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:20 HGST 
                  |         `-- 51 x end_device -- disk
                  |--4x--expander-10:7 HGST 
                  |      |--1x--end_device-10:7:0
                  |      |      `--enclosure io8-jbod7 HGST 
                  |      |--10x--expander-10:21 HGST 
                  |      |  `-- 51 x end_device -- disk
                  |      `--10x--expander-10:22 HGST 
                  |         `-- 51 x end_device -- disk
                  `--4x--expander-10:8 HGST 
                         |--1x--end_device-10:8:0
                         |      `--enclosure io8-jbod8 HGST 
                         |--10x--expander-10:23 HGST 
                         |  `-- 51 x end_device -- disk
                         `--10x--expander-10:24 HGST 
                            `-- 51 x end_device -- disk


Use ``sas_discover --counters`` to display the number of SCSI commands issued (`req`), completed or rejected (`done`) and the ones that completed with an error (`error`).

.. image:: https://raw.githubusercontent.com/stanford-rc/sasutils/master/doc/examples/sas_discover_counters_tape.svg


sas_devices
-----------

Zeroconf tool that scans SAS devices and resolves associated enclosures. Useful to quickly check cabling and hardware setup.

When used with -v, **sas_devices** will also display all disk devices with serial numbers.

The following example shows a proper detection of a 60-disk JBOD with 2 SIMs/IOMs (an "enclosure group").

    .. code-block::

        $ sas_devices
        Found 2 SAS hosts
        Found 4 SAS expanders
        Found 1 enclosure groups
		Enclosure group: [io1-jbod1-0][io1-jbod1-1]
		NUM         VENDOR            MODEL    REV     SIZE  PATHS
		 60 x      SEAGATE     ST8000NM0075   E004    8.0TB      2
        Total: 60 block devices in enclosure group


The following example shows a proper detection of four Seagate Exos E JBOFs with 15.4TB SSDs. Note that 2 IOMs are detected for each JBOF and they have the same SES-2 nickname (this is normal with this hardware).

    .. code-block::

        $ sas_devices
        Found 2 SAS hosts
        Found 8 SAS expanders
        Found 4 enclosure groups
        Enclosure group: [io1-jbof4][io1-jbof4]
        NUM         VENDOR            MODEL    REV     SIZE  PATHS
         24 x      SEAGATE   XS15360SE70084   0003   15.4TB      2
        Total: 24 block devices in enclosure group
        Enclosure group: [io1-jbof2][io1-jbof2]
        NUM         VENDOR            MODEL    REV     SIZE  PATHS
         24 x      SEAGATE   XS15360SE70084   0003   15.4TB      2
        Total: 24 block devices in enclosure group
        Enclosure group: [io1-jbof3][io1-jbof3]
        NUM         VENDOR            MODEL    REV     SIZE  PATHS
         24 x      SEAGATE   XS15360SE70084   0003   15.4TB      2
        Total: 24 block devices in enclosure group
        Enclosure group: [io1-jbof1][io1-jbof1]
        NUM         VENDOR            MODEL    REV     SIZE  PATHS
         24 x      SEAGATE   XS15360SE70084   0003   15.4TB      2
        Total: 24 block devices in enclosure group


ses_report
----------

SES status and environmental metrics.

Used with -c, this command will find all enclosures and then use SES-2 nicknames and use sg_ses to output results suitable for Carbon/Graphite.

    .. code-block::

        $ ses_report -c --prefix=datacenter.stanford
        datacenter.stanford.io1-sassw1.Cooling.Left_Fan.speed_rpm 19560 1476486766
        datacenter.stanford.io1-sassw1.Cooling.Right_Fan.speed_rpm 19080 1476486766
        datacenter.stanford.io1-sassw1.Cooling.Center_Fan.speed_rpm 19490 1476486766
        ...

Use -s to get the status of all detected SES Element Descriptors.

    .. code-block::

        # ses_report -s --prefix=datacenter.stanford | grep SIM
        datacenter.stanford.io1-jbod1-0.Enclosure_services_controller_electronics.SIM_00 OK
        datacenter.stanford.io1-jbod1-0.Enclosure_services_controller_electronics.SIM_01 OK
        datacenter.stanford.io1-jbod1-0.SAS_expander.SAS_Expander_SIM_0 OK
        datacenter.stanford.io1-jbod1-0.SAS_expander.SAS_Expander_ISIM_2 OK
        datacenter.stanford.io1-jbod1-0.SAS_expander.SAS_Expander_ISIM_0 OK
        datacenter.stanford.io1-jbod1-1.Enclosure_services_controller_electronics.SIM_00 OK
        datacenter.stanford.io1-jbod1-1.Enclosure_services_controller_electronics.SIM_01 OK
        datacenter.stanford.io1-jbod1-1.SAS_expander.SAS_Expander_SIM_1 OK
        datacenter.stanford.io1-jbod1-1.SAS_expander.SAS_Expander_ISIM_3 OK
        datacenter.stanford.io1-jbod1-1.SAS_expander.SAS_Expander_ISIM_1 OK

.. warning::

       **ses_report** requires a recent version of *sg3_utils* and won't work with the version shipped with CentOS 6 for example.


sas_sd_snic_alias and sas_st_snic_alias
---------------------------------------

Generate udev aliases using the SES-2 subenclosure nickname and bay identifier of each device.
These scripts can also be used as examples and adapted to your specific needs.

For example, for block devices, add the following to your udev rules:

    .. code-block::

        KERNEL=="sd*", PROGRAM="/usr/bin/sas_sd_snic_alias %k", SYMLINK+="%c"

Or, for SAS tape drives behind SAS switches (that act as enclosures):

    .. code-block::

        KERNEL=="st*", PROGRAM="/usr/bin/sas_st_snic_alias %k", SYMLINK+="%c"

This should generate udev aliases made of the device subenclosure nickname followed by the bay identifier. In the following case, *io1-jbod1-0* is the subenclosure nickname (here SIM 0 of JBOD #1).

    .. code-block::

        $ ls -l /dev/io1-jbod1-0-bay26
        lrwxrwxrwx 1 root root 4 Oct 14 21:00 /dev/io1-jbod1-0-bay26 -> sdab

.. note::

       Use `sg_ses --nickname=...` to define SES-2 subenclosure nicknames.

sas_mpath_snic_alias
--------------------

This utility is very similar to **sas_sd_snic_alias** but only accepts device-mapper devices. Add the following line to your udev rules:

    .. code-block::

        KERNEL=="dm-[0-9]*", PROGRAM="/usr/bin/sas_mpath_snic_alias %k", SYMLINK+="mapper/%c"

This will result in useful symlinks.

    .. code-block::

        $ ls -l /dev/mapper/io1-jbod1-bay26
        lrwxrwxrwx 1 root root 8 Oct 14 21:00 /dev/mapper/io1-jbod1-bay26 -> ../dm-31

.. note::

       For **sas_mpath_snic_alias** to work with a JBOD having two SIMs, both enclosure nicknames should have a common prefix (eg. "myjbodX-") that will be automatically used.


sasutils Python library
=======================

Documentation will be available on the `wiki`_.

* the following example will list all SAS hosts (controllers) found in sysfs

    .. code-block:: python

        from sasutils.sas import SASHost
        from sasutils.sysfs import sysfs

        # sysfs is a helper to walk through sysfs (/sys)
        for node in sysfs.node('class').node('sas_host'):

            # Instantiate SASHost with the sas_host sysfs device class
            host = SASHost(node.node('device'))

            # To get its sysfs name, use:
            print(host.name)
            # To get attributes from scsi_host, use:
            print('  %s' % host.scsi_host.attrs.host_sas_address)
            print('  %s' % host.scsi_host.attrs.version_fw)

* See also https://github.com/stanford-rc/sasutils/wiki/Code-snippets

:Author: Stephane Thiell - Stanford Research Computing Center

.. _wiki: https://github.com/stanford-rc/sasutils/wiki
