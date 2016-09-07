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

from setuptools import setup, find_packages

VERSION = '0.1.2'

setup(name='sasutils',
      version=VERSION,
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      author='Stephane Thiell',
      author_email='sthiell@stanford.edu',
      license='Apache Software License',
      url='https://github.com/stanford-rc/python-sasutils',
      platforms=['GNU/Linux'],
      keywords=['SAS'],
      description='Python SAS utils',
      entry_points = {
            'console_scripts': [
                'sas_discover=sasutils.cli.sas_discover:main',
                'sas_blkdev_snic_alias=sasutils.cli.sas_blkdev_snic_alias:main'
            ],
      }
     )
