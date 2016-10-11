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

* the following example will list all SAS expanders found in sysfs

    .. code-block:: python

        from sasutils.sas import SASExpander
        from sasutils.sysfs import sysfs

        # sysfs is a helper to walk through sysfs (/sys)
        for node in sysfs.node('class').node('sas_expander'):

            # Instantiate SASExpander with the sas_expander sysfs device class
            expander = SASExpander(node.node('device'))

            # To get its sysfs name, use:
            print(expander.name)
            # To access its attributes, use:
            print('  %s' % expander.attrs.product_id)
            # To get attributes from the sas_device sysfs class, use:
            print('  %s' % expander.sas_device.attrs.sas_address)


:Author: Stephane Thiell

.. _Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0

