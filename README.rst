sasutils is a set of command-line tools and a Python library to ease the administration of Serial Attached SCSI (SAS) fabrics.

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

* sas_devices
* sas_discover
* ses_report

Also, two "zeroconf" udev scripts for use in udev rules that create friendly device aliases using SES-2 subenclosure nicknames.

* sas_mpath_snic_alias
* sas_sd_snic_alias

sas_discover
------------

Display SAS topology. By default, **sas_discover** tries to fold common devices (like disks). Use -v, -vv or -vvv to display more details.

    .. code-block::

        $ sas_discover -v
        oak-io1-s1
        |--host35 SAS9300-8e
        |  `---8x--expander-35:0 ASTEK 
        |          |---4x--expander-35:1 QCT 
        |          |       |--(60x)-end_device 60 x [disk]
        |          |       `---1x--end_device-35:1:60 [enclosure] io1-jbod1-0
        |          `---1x--end_device-35:0:0 [enclosure] io1-sassw1
        `--host36 SAS9300-8e
           `---8x--expander-36:0 ASTEK 
                   |---4x--expander-36:1 QCT 
                   |       |--(60x)-end_device 60 x [disk]
                   |       `---1x--end_device-36:1:60 [enclosure] io1-jbod1-1
                   `---1x--end_device-36:0:0 [enclosure] io1-sassw2


sas_devices
-----------

Zeroconf tool that scans SAS devices and resolves associated enclosures. Useful to quickly check cabling and hardware setup.

When used with -v, **sas_devices** will also display all disk devices with serial numbers.

The following example shows a proper detection of a 60-disk JBOD with 2 SIMs (an "enclosure group").

    .. code-block::

        $ sas_devices
        Found 2 SAS hosts
        Found 4 SAS expanders
        Found 1 enclosure groups
        Enclosure group: [io1-jbod1-0][io1-jbod1-1]
        NUM         VENDOR        MODEL    REV  PATHS
         60 x      SEAGATE ST8000NM0075   E002      2
        Total: 60 block devices in enclosure group


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


sas_sd_snic_alias
-----------------

Generate udev aliases using the SES-2 subenclosure nickname and bay identifier of each device.

For example, add the following to your udev rules:

    .. code-block::

        KERNEL=="sd*", PROGRAM="/usr/bin/sas_sd_snic_alias %k", SYMLINK+="%c"

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
