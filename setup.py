#!/usr/bin/python
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

from setuptools import setup, find_packages

VERSION = '0.1.5'

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
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Systems Administration'
      ],
      entry_points = {
            'console_scripts': [
                'sas_devices=sasutils.cli.sas_devices:main',
                'sas_discover=sasutils.cli.sas_discover:main',
                'sas_sd_snic_alias=sasutils.cli.sas_sd_snic_alias:main',
                'ses_report=sasutils.cli.ses_report:main'
            ],
      }
     )
