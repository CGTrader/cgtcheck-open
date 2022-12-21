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
Common functionality for blender tests
"""
import os

import bpy
import threed


def get_temp_file(tmpdir: str):
    """
    Saved empty temporary blender file in temporary directory
    """
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    filepath = os.path.join(tmpdir, 'tmp.blend')
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    bpy.ops.object.select_all(action='DESELECT')
    return filepath


def reset_blender_scene():
    threed.blender.common.reset()


def scene_with_named_entities(request_param):
    """
    Adds boxes with materials to the scene and empties.
    Object names and quantity are configured according to fixture parameters.
    """
    reset_blender_scene()
    objects = []
    for obj_type in request_param:
        for name in request_param[obj_type]:
            if obj_type == 'meshes':
                bpy.ops.mesh.primitive_cube_add()
                obj = bpy.context.active_object
                obj.name = name
            elif obj_type == 'empties':
                bpy.ops.object.empty_add()
                obj = bpy.context.active_object
                obj.name = name
            else:
                mat = bpy.data.materials.new(name)
                objects[0].data.materials.append(mat)
            objects.append(obj)

    return tuple(objects)
