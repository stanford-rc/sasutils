sasutils is a set of command-line tools and a Python library to ease the
administration of Serial Attached SCSI (SAS) fabrics.

.. image:: https://img.shields.io/pypi/v/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/

.. image:: https://img.shields.io/pypi/pyversions/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/
    :alt: Supported Python Versions

.. image:: https://img.shields.io/pypi/l/sasutils.svg
    :target: https://pypi.python.org/pypi/sasutils/
    :alt: License

CLI tools
---------

* sas_devices
* sas_discover
* ses_report

udev tools
----------

zeroconf scripts for use in udev rules that create friendly device aliases
using SES-2 subenclosure nicknames.

* sas_mpath_snic_alias
* sas_snic_snic_alias

Example usage
-------------

* sas_discover

Display SAS topology. Use -v, -vv or -vvv to display more details.

.. code-block:: none

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

* ses_report

Used with -c, this command will find all enclosures and then use SES-2
nicknames and use sg_ses to output results suitable for Carbon/Graphite.

.. code-block:: none

    $ ses_report -c --prefix=datacenter.stanford
    datacenter.stanford.io1-sassw1.Cooling.CoolingElementInSubEnclsr0.speed_rpm 0 1476486766
    datacenter.stanford.io1-sassw1.Cooling.Left_Fan.speed_rpm 19560 1476486766
    datacenter.stanford.io1-sassw1.Cooling.Right_Fan.speed_rpm 19080 1476486766
    datacenter.stanford.io1-sassw1.Cooling.Center_Fan.speed_rpm 19490 1476486766
    ...


Example usage (Python)
----------------------

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

:Author: Stephane Thiell
