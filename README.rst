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
