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

from contextlib import contextmanager
from math import radians
from typing import Sequence, Any, List

import bpy
import bpy_types
from mathutils import Vector, Matrix

import threed.blender.animation as threed_animation
import threed.blender.dimensions as threed_dimensions

AXIS_NAME_TO_VECT = {
    '+X': Vector((1, 0, 0)),
    '-X': Vector((-1, 0, 0)),
    '+Y': Vector((0,  1, 0)),
    '-Y': Vector((0, -1, 0)),
    '+Z': Vector((0, 0,  1)),
    '-Z': Vector((0, 0, -1)),
}
AXIS_NAME_TO_VECT['X'] = AXIS_NAME_TO_VECT['+X']
AXIS_NAME_TO_VECT['Y'] = AXIS_NAME_TO_VECT['+Y']
AXIS_NAME_TO_VECT['Z'] = AXIS_NAME_TO_VECT['+Z']


def get_mesh_objects():
    # type: () -> list[bpy_types.Object]
    """
    Returns a list of all objects of the "MESH" type only.
    """
    return [obj for obj in bpy.data.objects if obj.type == 'MESH']


def material_index(mesh, material):
    """
    Return the index of the specified material in the specified mesh
    If material is not found in the mesh, return -1
    """

    for i, m in enumerate(mesh.materials):
        if m == material:
            return i
    return -1


def stats_from_blender(stat):
    # type: (str) -> str | int
    """
    Returns chosen blender statistic. These statistics can be
    seen in the bottom right corner of Blender 2.8+ window.
    First two items from statistics list are not included:
    "Collection" and selected object name.

    Keyword Arguments:
            Verts   -- number of vertices.
            Tris    -- number of triangles.
            Faces   -- number of faces.
            Objects -- number of objects (result depends on if anything selected).
            Memory  -- memory in MiB (result depends on if anything selected).
            Version -- current version of Blender that the script is run on.

    Returns:
        stat -- returns one of stats from blender.
                For 'Verts', 'Faces', 'Tris' return integer, for others - string.
    """
    statistics = bpy.context.scene.statistics(bpy.context.view_layer)
    st_list = list(statistics.split(" | "))

    st_dict = {'Objects': [i for i in st_list if i.startswith('Objects')][0][8:],
               'Version': [i for i in st_list if i.startswith(('v2', '2.', '3.'))][0],
               'Memory': [i for i in st_list if i.startswith('Mem')][0][5:],
               'Verts': int([i for i in st_list if i.startswith('Verts')][0][6:].replace(",", "")),
               'Faces': int([i for i in st_list if i.startswith('Faces')][0][6:].replace(",", "")),
               'Tris': int([i for i in st_list if i.startswith('Tris')][0][5:].replace(",", ""))}

    return st_dict[stat]


def mesh_triangle_count(mesh):
    # type: (bpy_types.Mesh) -> int
    """
    Return the triangle count for the mesh
    """
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def reset():
    """
    Resets blender state
    """

    collections = (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.images,
        bpy.data.actions,
    )
    for col in collections:
        for obj in col:
            col.remove(obj, do_unlink=True)

    extras = ('EMPTY', 'ARMATURE')
    for extra in bpy.data.objects:
        if extra.type in extras:
            bpy.data.objects.remove(extra, do_unlink=True)


def sort_by_hierarchy(objects, add_children=True):
    # type: (list[bpy_types.Object], bool) -> list[list[bpy_types.Object]]
    """
    Sorts given objects into groups by top level parents.
    Each group will have its root as first object in list, followed by its children.
    Objects with parents, are considered "root" if their parent is outside of given collection.

    Args:
        objects: collection of objects to sort into hierarchies
        add_children: if True, any child objects will be added, if False, the resulting groups
                      will contain only objects from the initial `objects` collection

    Returns:
        List of lists of objects.
        Each internal list contains objects sorted by hierarchy, parents before children;
        each beginning with top level object (one which doesn't have a parent, or its parent
        is not within the provided 'objects' collection)
    """
    obj_set = set(objects)
    roots = (obj for obj in objects if obj.parent not in obj_set)
    return [
        [obj for obj in hierarchy(root) if add_children or obj in obj_set]
        for root in roots
    ]


def hierarchy(obj):
    # type: (bpy_types.Object) -> list[bpy_types.Object]
    """
    Iterator over object and all its children. Children are returned depth-first.
    """
    yield obj
    for child in obj.children:
        yield from hierarchy(child)  # noqa E999


def select_objects(objects):
    """
    Selects given objects
    """

    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)


def is_mesh_instanced(obj):
    # type: (bpy_types.Object) -> bool
    """
    Checks if the passed object has an instanced (linked) mesh connected to other objects
    """
    if not hasattr(obj, 'data') or not obj.data:
        return False
    return obj.data.users > 1


def transform_apply(objects, apply_instances=True, top_level=True, children=True):
    # type: (list[bpy_types.Object], bool, bool, bool) -> None
    """
    Sets the transforms to 0 while retaining their positions.

    WARNING: Only applying top_level transforms modifies the children objects' transform values,
    but they remain in place relative to World.

    Args:
        objects (list[bpy_types.Object]):  scene objects to apply transforms to
        apply_instances (bool): make instances into duplicates,
                                           then apply their transforms
        children (bool): also apply transforms to child objects
        top_level (bool): also apply transforms to top-level objects
    """
    if not (top_level or children):
        return
    objects_to_apply = objects
    sorted_by_hierarchy = sort_by_hierarchy(objects_to_apply)
    sorted_by_hierarchy_filtered = []
    for branch in sorted_by_hierarchy:
        if not top_level:
            branch = branch[1:]
        # Keep only the first (top) node if children (bool) was set to false OR
        # if instances do not need to have their transforms reset (apply_instances (bool) is False),
        # yet they were found deeper down the hierarchy.
        if not children or ((not apply_instances)
                            and any(obj for obj in branch if is_mesh_instanced(obj))):
            if len(branch) > 1:
                branch = branch[:1]
        if not branch:
            continue
        sorted_by_hierarchy_filtered.append(branch)
    for branch in sorted_by_hierarchy_filtered:
        for obj in branch:
            with selection([obj]):
                bpy.ops.object.make_single_user(object=True, obdata=True)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def place_model_at_origin(objects=None, animated=False,
                          transforms_apply=True,
                          transforms_apply_instances=True,
                          transforms_apply_top_level=True,
                          transforms_apply_children=True):
    # type: (list[bpy_types.Object], bool, bool, bool, bool, bool) -> None
    """
    Places all scene's mesh objects at origin, lowest Z coordinate at 0.
    Applies transforms if 'animated' is False AND 'transforms_apply' is True.
    """
    if objects is None:
        objects = bpy.data.objects

    meshes = [obj for obj in objects if obj.type == "MESH"]
    meshes_offset = Vector(threed_dimensions.get_scene_bottom_center(objects=meshes))

    groups = sort_by_hierarchy(objects)
    for gr in groups:
        obj = gr[0]
        if animated:
            threed_animation.move_animated(obj, -meshes_offset)
        else:
            obj.location -= meshes_offset

    if not animated and transforms_apply:
        transform_apply(objects=objects,
                        apply_instances=transforms_apply_instances,
                        top_level=transforms_apply_top_level,
                        children=transforms_apply_children)


def move_objects_pivot(objects, world_location):
    # type: (Sequence[bpy_types.Object], Vector) -> None
    """
    Move objects' pivots to a specified location.
    A location of Vector((0, 0, 0)) will move the pivots to the scene's origin.

    Args:
        objects (Sequence[bpy_types.Object]): objects the pivots of which will be moved
        world_location (mathutils.Vector): world location where the pivots will be moved to
    """

    for obj in objects:
        with selection([obj]):
            with cursor('location', world_location):
                obj_mw = obj.matrix_world
                cursor_local_loc = obj_mw.inverted() @ world_location
                mesh = obj.data
                mesh.transform(Matrix.Translation(-cursor_local_loc))
                obj_mw.translation = world_location


def pivot_to_mount_point(objects, axis):
    # type: (list[bpy_types.Object], str) -> None
    """
    Places the pivot at the objects' collective bounding box plane center (mount point).
    """
    mount_point = threed_dimensions.get_mount_point(objects=objects, axis=axis)
    move_objects_pivot(objects=objects, world_location=Vector(mount_point))


def merge_objects(objects):
    # type: (Sequence[bpy_types.Object]) -> list[bpy_types.Object]
    """
    Merges provided objects (and their geometry) into one.
    The resulting object is named after the first one in the "objects" sequence.
    """

    bpy.context.view_layer.objects.active = objects[0]
    select_objects(objects)
    bpy.ops.object.join()

    # Return the resulting merged object(s). This filters out the no-longer-existing objects.
    return [obj for obj in objects if obj in bpy.data.objects.values()]


def flip_all_objects() -> None:
    """
    Flips all objects upside down by turning them 180 degrees on the X axis along world origin.
    Currently, only supports non-animated objects.
    """
    objects = [
        o for o in bpy.data.objects
        if o.type in ('MESH', 'EMPTY')
        and o.parent is None
    ]
    for top_of_hierarchy in objects:
        # this rotates objects along world origin (0, 0, 0)
        # it's the same as selecting all objects and rotating them
        top_of_hierarchy.matrix_world = (
            Matrix.Rotation(radians(180), 4, 'X') @ top_of_hierarchy.matrix_world
        )
    bpy.context.view_layer.update()  # without this the values won't be updated if accessed thru API


def remove_non_default_mat_nodes(material):
    """
    Remove non-default nodes from material, e.g.: detach maps that came attached
    with FBX file.

    Args:
        material (bpy.types.Material): e.g., bpy.data.materials['material_name']
    """

    nodes = material.node_tree.nodes

    for node in nodes:
        if node.name not in ["Material Output", "Principled BSDF", "Normal Map"]:
            nodes.remove(nodes[node.name])


def remove(
    meshes=False,
    materials=False,
    cameras=False,
    lights=False,
    empties=False,
    images=False,
    vertex_colors=False,
    animation=False,
    actions=False,
    shape_keys=False,
):
    """
    Removes unnecessary data from scene: preexisting materials and objects
    """
    data = bpy.data
    ops = bpy.ops

    if meshes:
        for mesh in data.meshes:
            data.meshes.remove(mesh, do_unlink=True)

    if materials:
        for mat in data.materials:
            data.materials.remove(mat, do_unlink=True)

    if lights:
        for light in data.lights:
            data.lights.remove(light, do_unlink=True)

    if cameras:
        for camera in data.cameras:
            data.cameras.remove(camera, do_unlink=True)

    if empties:
        for empty in data.objects:
            if empty.type == 'EMPTY':
                data.objects.remove(empty, do_unlink=True)

    if images:
        for image in data.images:
            data.images.remove(image, do_unlink=True)

    if vertex_colors:
        ops.mesh.vertex_color_remove()

    if animation:
        ops.anim.keyframe_clear_v3d()

    if actions:
        for action in data.actions:
            data.actions.remove(action, do_unlink=True)

    if shape_keys:
        for obj in bpy.data.objects:
            obj.shape_key_clear()


@contextmanager
def selection(objects):
    """
    Selects input objects at enter and restores previous selection at exit.
    """
    previous_selection = bpy.context.selected_objects
    select_objects(objects)
    yield
    select_objects(previous_selection)


@contextmanager
def activation(obj):
    """
    Sets input object as active at enter and restores previously active object at exit.
    """
    previously_active = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    yield
    bpy.context.view_layer.objects.active = previously_active


def make_single_user(objects, object=False, obdata=False, material=False, animation=False):
    """
    Wrapper for making multiple objects single-user.
    """
    with selection(objects):
        for obj in objects:
            with activation(obj):
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS',
                                                object=object,
                                                obdata=obdata,
                                                material=material,
                                                animation=animation)


@contextmanager
def keep_instances(objects):
    """
    Makes objects single-user, performs the callback's operation, recreates instances.
    Args:
        objects (list[bpy_types.Object]): objects to call the callback on.
    Returns:
        Generator object of the callback's results.
    """
    objs_with_a_mesh = [obj for obj in objects if obj.type == "MESH"]
    unique_meshes = set(obj.data.original for obj in objs_with_a_mesh)
    unique_meshes_their_objs = dict()
    unique_meshes_their_objs_names = dict()

    for unique_mesh in unique_meshes:
        associated_objects = [o for o in objs_with_a_mesh if o.data is unique_mesh]
        unique_meshes_their_objs[unique_mesh] = associated_objects
        unique_meshes_their_objs_names[unique_mesh.name] = [o.name for o in associated_objects]

    for _, associated_objects in unique_meshes_their_objs.items():
        make_single_user(objects=associated_objects, object=True, obdata=True)

    yield

    for mesh_name, associated_object_names in unique_meshes_their_objs_names.items():
        associated_objects_temp = []
        for associated_object_name in associated_object_names:
            associated_object = bpy.data.objects[associated_object_name]
            associated_objects_temp.append(associated_object)
        mesh = bpy.data.meshes[mesh_name]
        for associated_object in associated_objects_temp:
            associated_object.data = mesh


@contextmanager
def cursor(attr, value):
    # type: (str, Any) -> None
    """
    Sets bpy.context.scene.cursor "attr" to "value" at enter, restores initial "value" upon exiting.

    Args:
        attr (str): Attribute name of "bpy.context.scene.cursor" to be changed.
        value (Any): Value to set this attribute to.
    """
    try:
        initial_cursor_attr_value = getattr(bpy.context.scene.cursor, attr).copy()
    except AttributeError:
        initial_cursor_attr_value = getattr(bpy.context.scene.cursor, attr)
    setattr(bpy.context.scene.cursor, attr, value)
    yield
    setattr(bpy.context.scene.cursor, attr, initial_cursor_attr_value)
