#
# Copyright (C) 2016, 2017, 2018, 2019, 2021, 2022, 2023
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

from setuptools import setup, find_packages

VERSION = '0.6.0'

setup(name='sasutils',
      version=VERSION,
      packages=find_packages(),
      author='Stephane Thiell',
      author_email='sthiell@stanford.edu',
      license='Apache Software License',
      url='https://github.com/stanford-rc/sasutils',
      platforms=['GNU/Linux'],
      keywords=['SAS', 'SCSI', 'storage'],
      description='Serial Attached SCSI (SAS) Linux utilities',
      long_description=open('README.rst').read(),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Systems Administration'
      ],
      entry_points={
          'console_scripts': [
              'sas_counters=sasutils.cli.sas_counters:main',
              'sas_devices=sasutils.cli.sas_devices:main',
              'sas_discover=sasutils.cli.sas_discover:main',
              'sas_mpath_snic_alias=sasutils.cli.sas_mpath_snic_alias:main',
              'sas_sd_snic_alias=sasutils.cli.sas_sd_snic_alias:main',
              'sas_st_snic_alias=sasutils.cli.sas_st_snic_alias:main',
              'ses_report=sasutils.cli.ses_report:main'
          ],
      },
      )
