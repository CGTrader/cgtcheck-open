# This code is provided to you by UAB CGTrader, code 302935696, address - Antakalnio str. 17,
# Vilnius, Lithuania, the company registered with the Register of Legal Entities of the Republic
# of Lithuania (CGTrader).
#
# Copyright (C) 2022  CGTrader.
#
# This program is provided to you as free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version. It is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public License along with this
# program. If not, see https://www.gnu.org/licenses/.

from pathlib import Path
import setuptools


PACKAGE_NAME = 'cgtcheck-open'
parent_dir = Path(__file__).parent
long_description = (parent_dir / 'README.md').read_text()

version_namespace = {}
version_file = parent_dir / '_version.py'
exec(version_file.read_text(), version_namespace)


setuptools.setup(
    name=PACKAGE_NAME,
    version=version_namespace['__version__'],
    author='CGTrader',
    author_email='opensource@cgtrader.com',
    description='Perform asset validation',
    long_description=long_description,
    url='https://github.com/CGTrader/cgtcheck-open',
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.7',
    license_files=['LICENSE'],
)
