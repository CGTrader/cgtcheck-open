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

"""
Functionality related to file formats
"""

from re import finditer
from struct import unpack
from typing import Tuple, Optional


def fbx_version(filepath: str) -> Tuple[bool, Optional[int]]:
    """
    Returns version information for FBX file. Indicating whether the file
    is binary (True) or ASCII (False) and the version number (in raw notation, e.g. 7400).

    Args:
        filepath: location of the file

    Returns:
        Tuple of:
            [0] bool indicating that the file is binary, False suggests ASCII
            [1] int representing the version, may be None, if it is not found in ASCII file
    """
    with open(filepath, mode='rb') as f:
        content = f.read(27)
        if len(content) < 27:
            raise IOError('FBX file is corrupt (not enough content)')
        is_binary = content.startswith(b'Kaydara FBX Binary  \x00')  # expected header
        if is_binary:
            version, *_ = unpack('i', content[-4:])
        else:
            f.seek(0)
            content = f.read()
            version_match = next(finditer(rb'FBXVersion:\s*(\d+)', content), None)
            if version_match is None:
                raise IOError("Unable to find 'FBXVersion' in assumed ASCII FBX file")
            version = int(version_match.groups()[0])

    return (is_binary, version)
