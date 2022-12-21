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

from sys import float_info

import bpy
import bpy_types
from mathutils import Vector


def object_bounds(obj):
    """
    Takes blender object and returns its bounding box.

    Args:
        obj (bpy_struct): blender object.

    Returns:
        [list]: object dimensions [[minus_x, minus_y, minus_z],
                [plus_x, plus_y, plus_z]]
    """

    min_x, min_y, min_z = (float_info.max,) * 3
    max_x, max_y, max_z = (-float_info.max,) * 3

    for vertex in obj.bound_box:
        world_vertex = obj.matrix_world @ Vector(vertex)
        x, y, z = world_vertex.x, world_vertex.y, world_vertex.z

        if x < min_x: min_x = x # noqa E701
        if y < min_y: min_y = y # noqa E701
        if z < min_z: min_z = z # noqa E701

        if x > max_x: max_x = x # noqa E701
        if y > max_y: max_y = y # noqa E701
        if z > max_z: max_z = z # noqa E701

    bounds_min = [min_x, min_y, min_z]
    bounds_max = [max_x, max_y, max_z]

    return [bounds_min, bounds_max]


def get_bounding_box(objects=None, selected=False):
    # type: (list[object], bool) -> tuple[tuple[float, float, float], tuple[float, float, float]]
    """
    Returns axis-aligned bounding box (defined by two opposite corners)
    for given objects.

    Args:
        selected (bool, optional): if True - works with selected objects.
            Otherwise - with all the meshes in the scene. Defaults to False.
            Has no effect if 'objects' argument is used instead.
        objects (list, optional): will calculate AABB for these objects, if given

    Return:
        list (list)
            [0] (list float[3]) min point, x/y/z
            [1] (list float[3]) max point, x/y/z
    """

    if objects is None:
        if selected:
            objects = bpy.context.selected_objects
        else:
            objects = list(bpy.context.scene.objects)

    min_x, min_y, min_z = (float_info.max,) * 3
    max_x, max_y, max_z = (-float_info.max,) * 3

    for obj in objects:
        bounds = object_bounds(obj)

        ox_min = bounds[0][0]
        ox_max = bounds[1][0]

        oy_min = bounds[0][1]
        oy_max = bounds[1][1]

        oz_min = bounds[0][2]
        oz_max = bounds[1][2]

        # min

        if ox_min < min_x:
            min_x = ox_min

        if oy_min < min_y:
            min_y = oy_min

        if oz_min < min_z:
            min_z = oz_min

        # max

        if ox_max > max_x:
            max_x = ox_max

        if oy_max > max_y:
            max_y = oy_max

        if oz_max > max_z:
            max_z = oz_max

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def get_scene_bounds(objects=None, selected=False):
    """
    Returns bounding-box dimensions of multiple objects.

    Args:
        selected (bool, optional): if True - works with selected objects.
            Otherwise - with all the meshes in the scene. Defaults to False.
            Has no effect if 'objects' argument is used instead.
        objects (list, optional): will calculate AABB for these objects, if given
    """

    bb_min, bb_max = get_bounding_box(objects=objects, selected=selected)

    return (bb_max[0] - bb_min[0],  # X
            bb_max[1] - bb_min[1],  # Y
            bb_max[2] - bb_min[2])  # Z


def get_scene_bottom_center(objects=None, selected=False):
    """
    Returns bottom center pivot/origin location for multiple objects.

    Args:
        selected (bool, optional): if True - works with selected objects.
            Otherwise - with all the meshes in the scene. Defaults to False.
            Has no effect if 'objects' argument is used instead.
        objects (list, optional): will calculate center for these objects, if given
    """

    bb_min, bb_max = get_bounding_box(objects=objects, selected=selected)

    return (
        (bb_min[0] + bb_max[0]) * 0.5,  # X
        (bb_min[1] + bb_max[1]) * 0.5,  # Y
        bb_min[2]                       # Z
    )


def get_scene_center(objects=None, selected=False):
    """
    Returns center pivot/origin location for multiple objects.

    Args:
        selected (bool, optional): if True - works with selected objects.
            Otherwise - with all the meshes in the scene. Defaults to False.
            Has no effect if 'objects' argument is used instead.
        objects (list, optional): will calculate center for these objects, if given
    """

    bb_min, bb_max = get_bounding_box(objects=objects, selected=selected)

    return ((bb_min[0] + bb_max[0]) * 0.5,  # X
            (bb_min[1] + bb_max[1]) * 0.5,  # Y
            (bb_min[2] + bb_max[2]) * 0.5)  # Z


def get_mount_point(objects=None, selected=False, axis=None):
    # type: (list[bpy_types.Object], bool, str) -> list[float, float, float]
    """
    Returns the objects' mount point on an axis.

    Args:
        objects (Sequence, optional): will calculate center for these objects, if given.
        selected (bool, optional): if True - works with selected objects.
            Otherwise - with all the meshes in the scene. Defaults to False.
            Has no effect if 'objects' argument is used instead.
        axis (str): one of ('X', 'Y', 'Z', '-X', '-Y', '-Z') axes. '-Z' by default.
            '-Z' is set as default to mimic the behavior of get_scene_bottom_center,
            thus making this function easier to understand.

    Example:
        >>> import bpy
        >>> cube = bpy.data.objects['Cube']
        >>> get_mount_point(objects=[cube], axis='-Z')
        [0.0, 0.0, -1.0]


    Returns:
        xyz (list): X Y Z location coordinates of the objects' center on given axis
    """
    if axis is None:
        axis = '-Z'

    axes = ('X', 'Y', 'Z')

    bb_min, bb_max = get_bounding_box(objects=objects, selected=selected)

    xyz = []
    for i, axis_ in enumerate(axes):
        if axis_ in axis:
            xyz.append(bb_min[i] if axis.startswith('-') else bb_max[i])
            continue
        xyz.append((bb_min[i] + bb_max[i]) * 0.5)
    return xyz
