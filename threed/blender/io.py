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
File and other IO functionality
"""

import bpy

class ImportErrorException(Exception):
    pass


def import_fbx(filepath, anim_enabled=False):
    """
    Imports FBX.

    Args:
        file (str): filepath to FBX to import
        anim_enabled (bool): should animatons be imported?
    """

    if anim_enabled:
        bpy.context.scene.frame_start = 0

    try:
        bpy.ops.import_scene.fbx(filepath=filepath, use_anim=anim_enabled, anim_offset=0.0)
    except Exception as exc:
        msg = ""
        if exc.args[0].startswith("Error: ASCII FBX files are not supported"):
            msg = "ASCII FBX files are not supported."
        elif exc.args[0].startswith("Error: Version"):
            msg = (exc.args[0]).replace("Error: ", "")
        raise ImportErrorException("Failed to import FBX. {}".format(msg))
