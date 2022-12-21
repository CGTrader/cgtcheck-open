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

import os
import pytest
from inspect import currentframe
from typing import List

from PIL import Image
import bpy
import bmesh
from mathutils import Vector, Matrix
from math import radians
import cgtcheck
import cgtcheck.blender.all_checks
import cgtcheck.generic.all_checks
from cgtcheck.blender.tests.common_blender import reset_blender_scene


@pytest.fixture
def runner(request):
    runner = cgtcheck.runners.CheckRunner(checks_spec=request.param)
    yield runner
    runner.reset()


@pytest.fixture
def temp_file(tmpdir):
    from cgtcheck.blender.tests.common_blender import get_temp_file
    return get_temp_file(tmpdir)


@pytest.fixture
def create_empty_scene():
    """
    Creates an empty scene, without anything in it.
    """
    reset_blender_scene()


@pytest.fixture
def create_single_material_object() -> bpy.types.Object:
    """
    Adds basic test model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    mat = bpy.data.materials.new(name="Material")
    cube.data.materials.append(mat)
    cube.name = 'model_single_material'
    return cube


@pytest.fixture
def create_multiple_material_object() -> bpy.types.Object:
    """
    Adds basic test model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    base_mat = bpy.data.materials.new(name="Material")
    mat = bpy.data.materials.new(name="Material2")
    cube.data.materials.append(base_mat)
    cube.data.materials.append(mat)
    cube.name = 'model_multiple_material'
    return cube


@pytest.fixture
def textures_with_res(tmpdir: pytest.fixture, request: pytest.fixture) -> list[str]:
    texture_paths = []
    for texture_id, resolution in enumerate(request.param, start=1):
        texture_path = os.path.join(tmpdir, 'texture_{}.png'.format(texture_id))
        width, height = resolution
        img = Image.new('RGB', (width, height), color='white')
        img.save(texture_path)
        texture_paths.append(texture_path)

    return texture_paths


@pytest.fixture
def required_textures_dummy_file(tmpdir) -> str:
    texture_path = os.path.join(tmpdir, 'required_textures.png')

    img = Image.new('RGB', (1, 1), color=(0, 0, 0))
    img.save(texture_path)

    return texture_path


@pytest.fixture
def create_plane() -> bpy.types.Object:
    """
    Adds a plane to the scene.
    """
    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    plane.name = 'plane'
    return plane


@pytest.fixture
def create_shadow_plane(create_plane) -> bpy.types.Object:
    """
    Adds a plane with a transparent material to the scene (shadow plane).
    """
    shadow_plane = create_plane
    shadow_plane.name = 'shadow_plane'

    mat_blend = bpy.data.materials.new(name='Material')
    mat_blend.blend_method = 'BLEND'
    shadow_plane.data.materials.append(mat_blend)

    # Would be "True", but Blender's custom bool properties turn into int after export & import.
    shadow_plane['is_shadow_plane'] = 1

    return shadow_plane


@pytest.fixture
def create_basic_cube():
    """
    Adds basic cube model to the scene.
    """
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'basic_cube'

    return cube


@pytest.fixture
def create_basic_cube_and_monkey_head():
    """
    Adds basic cube and monkey head model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_monkey_add()
    monkey = bpy.context.active_object
    monkey.name = 'basic_monkey'
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'basic_cube'

    cube.select_set(state=False)
    monkey.select_set(state=False)

    return monkey, cube


@pytest.fixture
def create_smooth_normals_monkey_head():
    """
    Adds a basic monkey, but with smooth normals.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_monkey_add()
    smooth_normals_monkey = bpy.context.active_object
    smooth_normals_monkey.name = 'smooth_normals_monkey'

    smooth_normals_monkey.select_set(True)
    bpy.context.view_layer.objects.active = smooth_normals_monkey
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = smooth_normals_monkey.data
    bm = bmesh.from_edit_mesh(mesh)
    for face in bm.faces:
        face.select = True
    bmesh.update_edit_mesh(mesh)
    mesh.update()
    bpy.ops.mesh.set_normals_from_faces()

    bpy.ops.object.mode_set(mode='OBJECT')
    smooth_normals_monkey.select_set(False)

    # These are the attributes we checked to determine faceted geometry before.
    # If we ever start checking it that way again, the test will fail.
    for poly in smooth_normals_monkey.data.polygons:
        poly.use_smooth = False
    for edge in smooth_normals_monkey.data.edges:
        edge.use_edge_sharp = True

    return smooth_normals_monkey


@pytest.fixture
def create_cube_moved():
    """
    Adds moved cube to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.location = 1, 0, 1
    return cube


@pytest.fixture
def create_cube_rotated():
    """
    Adds rotated cube to the scene.
    """
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.rotation_euler = 0, 1, 1
    return cube


@pytest.fixture
def create_cube_scaled():
    """
    Adds scaled cube to the scene.
    """
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = 2, 2, 2
    return cube


@pytest.fixture
def create_non_uniform_scaled_cube():
    """
    Adds a non-uniformly scaled cube model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.scale = 1.5, 3, 0
    return cube


@pytest.fixture
def create_subdivided_monkey_head():
    """
    Adds a subdivided monkey head model to the scene.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_monkey_add()
    monkey = bpy.context.active_object
    monkey.name = 'basic_monkey'

    mesh = monkey.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=3, use_grid_fill=True)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    return monkey


@pytest.fixture
def create_cube_hierarchy():
    """
    Adds a cube hierarchy to the scene.
    """
    reset_blender_scene()
    cubes = []
    for _ in range(6):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cubes.append(cube)

    for i, cube in enumerate(cubes):
        if i == 0:
            continue
        cube.parent = cubes[i - 1]

    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.parent = cubes[0]

    return cubes


@pytest.fixture
def create_hard_cube():
    """
    Adds hard edged cube model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    hard_cube = bpy.context.active_object
    hard_cube.name = 'hard_cube'
    for edge in hard_cube.data.edges:
        edge.use_edge_sharp = True
    for poly in hard_cube.data.polygons:
        poly.use_smooth = True
    return hard_cube


@pytest.fixture
def create_ngon():
    """
    Adds ngon model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    ngon_cube = bpy.context.active_object
    ngon_cube.name = 'ngon'
    bm = bmesh.new()
    bm.from_mesh(ngon_cube.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.dissolve_verts(bm, verts=[bm.verts[0]])
    bm.to_mesh(ngon_cube.data)

    return ngon_cube


@pytest.fixture
def create_empty_geo_obj():
    """
    Adds empty geo model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    empty_obj = bpy.context.active_object
    empty_obj.name = 'empty_obj'
    bm = bmesh.new()
    bm.from_mesh(empty_obj.data)
    bmesh.ops.delete(bm, geom=bm.verts)
    bm.to_mesh(empty_obj.data)

    return empty_obj


@pytest.fixture
def create_one_empty_geo_obj_one_normal_obj():
    """
    Adds one empty geo model and one normal cube to the scene.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    empty_obj = bpy.context.active_object
    empty_obj.name = 'empty_obj'
    bm = bmesh.new()
    bm.from_mesh(empty_obj.data)
    bmesh.ops.delete(bm, geom=bm.verts)
    bm.to_mesh(empty_obj.data)

    bpy.ops.mesh.primitive_cube_add()
    normal_obj = bpy.context.active_object
    normal_obj.name = 'normal_obj'

    return empty_obj, normal_obj


@pytest.fixture
def create_one_vertex_obj():
    """
    Adds a plane consisting of one vertex to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    one_vertex_obj = bpy.context.active_object
    one_vertex_obj.name = 'one_vertex_obj'
    bm = bmesh.new()
    bm.from_mesh(one_vertex_obj.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=bm.verts[0:3])
    bm.to_mesh(one_vertex_obj.data)
    return one_vertex_obj


@pytest.fixture
def create_zero_angle_face_corners():
    """
    Adds zero-angle corners model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    zero_angle_cube = bpy.context.active_object
    zero_angle_cube.name = 'zero_angle_cube'
    bm = bmesh.new()
    bm.from_mesh(zero_angle_cube.data)
    bm.verts.ensure_lookup_table()
    for i in [1, 2, 4, 7]:
        vertex = bm.verts[i]
        vertex.co = vertex.co * Vector((0, 0, 1))
    bm.to_mesh(zero_angle_cube.data)

    return zero_angle_cube


@pytest.fixture
def create_bottom_center_position_cube():
    """
    Adds basic cube model and move it so that its centre point
    on the bottom bounding box is in the position 0,0,0.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'create_bottom_center_position_cube'
    bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL')

    return cube


@pytest.fixture
def create_zero_length_edge():
    """
    Adds zero-angle corners model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    zero_length_edge_cube = bpy.context.active_object
    zero_length_edge_cube.name = 'zero_length_edge_cube'
    bm = bmesh.new()
    bm.from_mesh(zero_length_edge_cube.data)
    for v in bm.verts:
        v.co = v.co * Vector((0, 0, 1))
    bm.to_mesh(zero_length_edge_cube.data)

    return zero_length_edge_cube


@pytest.fixture
def create_uv_outside_zero_one():
    """
    Adds model with multiple UV layers (outside and inside the 0 to 1 range) to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    uv_outside_zero_one = bpy.context.active_object
    uv_outside_zero_one.name = 'uv_outside_zero_one'

    correct_uv = uv_outside_zero_one.data.uv_layers.new(name="correct_uv")
    uv_outside_zero_one.data.uv_layers.active = correct_uv

    incorrect_uv = uv_outside_zero_one.data.uv_layers.new(name="incorrect_uv")
    uv_outside_zero_one.data.uv_layers.active = incorrect_uv

    for face in uv_outside_zero_one.data.polygons:
        for loop_idx in face.loop_indices:
            incorrect_uv.data[loop_idx].uv = (4.2, 4.2)

    incorrect_uv_2 = uv_outside_zero_one.data.uv_layers.new(name="incorrect_uv_2")
    uv_outside_zero_one.data.uv_layers.active = incorrect_uv_2

    return uv_outside_zero_one


@pytest.fixture
def create_no_uv_cube():
    """
    Adds model without UV layers.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    no_uv_cube = bpy.context.active_object
    no_uv_cube.name = 'no_uv_cube'
    uv_layers = no_uv_cube.data.uv_layers
    for uv_layer in uv_layers:
        uv_layers.remove(uv_layer)
    return no_uv_cube


@pytest.fixture
def create_two_no_uv_cubes():
    """
    Adds two model without UV layers.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    no_uv_cube = bpy.context.active_object
    no_uv_cube.name = 'no_uv_cube'
    uv_layers = no_uv_cube.data.uv_layers
    for uv_layer in uv_layers:
        uv_layers.remove(uv_layer)
    bpy.ops.mesh.primitive_cube_add()
    second_no_uv_cube = bpy.context.active_object
    second_no_uv_cube.name = 'second_no_uv_cube'
    uv_layers = second_no_uv_cube.data.uv_layers
    for uv_layer in uv_layers:
        uv_layers.remove(uv_layer)
    return no_uv_cube, second_no_uv_cube


@pytest.fixture
def create_no_uv_multimat_cube():
    """
    Adds model without UV layers.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'no_uv_multimat_cube'
    uv_layers = cube.data.uv_layers
    for uv_layer in uv_layers:
        uv_layers.remove(uv_layer)
    cube.data.materials.append(bpy.data.materials.new(name='mat0'))
    cube.data.materials.append(bpy.data.materials.new(name='mat1'))
    for i, face in enumerate(cube.data.polygons):
        face.material_index = i % 2
    return cube


@pytest.fixture
def create_two_uv_cube():
    """
    Adds model with 2 UV layers.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    multiple_uv_cube = bpy.context.active_object
    multiple_uv_cube.name = 'multiple_uv_cube'
    multiple_uv_cube.data.uv_layers.new(name='second_uv_layer')
    return multiple_uv_cube


@pytest.fixture
def create_no_faceted_cube():
    """
    Adds hard edged cube model to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    no_faceted_cube = bpy.context.active_object
    no_faceted_cube.name = 'no_faceted_cube'
    for i in [0, 1, 4, 5]:
        # the result of the following commands is visually identical
        no_faceted_cube.data.edges[i].use_edge_sharp = True
        no_faceted_cube.data.polygons[i].use_smooth = True

    return no_faceted_cube


@pytest.fixture
def create_parent_child_cubes():
    """
    Adds object in parent child relation.
    The child objects are moved form origin but pivots are at origin position.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    first_child = bpy.context.active_object
    bpy.ops.transform.translate(value=(4, 2, 3), orient_type='GLOBAL')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    first_child.name = 'first_child'

    bpy.ops.mesh.primitive_cube_add()
    second_child = bpy.context.active_object
    bpy.ops.transform.translate(value=(0, 4, 2), orient_type='GLOBAL')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    second_child.name = 'second_child'

    bpy.ops.mesh.primitive_cube_add()
    parent = bpy.context.active_object
    parent.name = 'parent'

    for obj in bpy.context.scene.objects:
        obj.select_set(True)

    bpy.ops.object.parent_set(type='OBJECT')

    return parent, first_child, second_child


@pytest.fixture
def create_two_cubes_not_at_origin():
    """
    Adds two basic cubes and move them from origin position 0,0,0.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'create_bottom_center_position_cube'
    bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL')

    bpy.ops.mesh.primitive_cube_add()
    second_cube = bpy.context.active_object
    second_cube.name = 'create_bottom_center_position_cube'
    bpy.ops.transform.translate(value=(0, 4, 2), orient_type='GLOBAL')

    return cube, second_cube


@pytest.fixture
def create_texture_obj(tmpdir):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    texture_cube = bpy.context.active_object
    texture_cube.name = 'texture_cube'

    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True
    texture_cube.data.materials.append(mat)

    img = Image.new('RGB', (5, 5), color='white')
    texture_path = os.path.join(tmpdir, 'texture.png')
    img.save(texture_path)

    image = bpy.data.images.load(filepath=texture_path)
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )

    return texture_cube


@pytest.fixture
def create_no_texture_obj(tmpdir: pytest.fixture):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    no_texture_cube = bpy.context.active_object
    no_texture_cube.name = 'no_texture_cube'

    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True
    no_texture_cube.data.materials.append(mat)

    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness']
    )

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Metallic']
    )

    return no_texture_cube


@pytest.fixture
def create_texture_obj_shared_color_rough_metallic(tmpdir):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    texture_cube = bpy.context.active_object
    texture_cube.name = 'texture_cube'

    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True
    texture_cube.data.materials.append(mat)

    img = Image.new('RGB', (5, 5), color='white')
    texture_path = os.path.join(tmpdir, 'texture.png')
    img.save(texture_path)

    image = bpy.data.images.load(filepath=texture_path)
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness']
    )

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Metallic']
    )

    return texture_cube


@pytest.fixture
def create_embedded_texture_obj(tmpdir):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    embedded_texture_cube = bpy.context.active_object
    embedded_texture_cube.name = 'embedded_texture_cube'

    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True
    embedded_texture_cube.data.materials.append(mat)

    img = Image.new('RGB', (5, 5), color='white')
    texture_path = os.path.join(tmpdir, 'embedded_texture.png')
    img.save(texture_path)

    image = bpy.data.images.load(filepath=texture_path)
    image.pack()
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )

    return embedded_texture_cube


@pytest.fixture
def create_texel_density_obj(tmpdir: pytest.fixture, request: pytest.fixture):
    densities = request.param

    cubes = []
    reset_blender_scene()
    for density in densities:
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cubes.append(cube)
        cube.name = 'cube'

        mat = bpy.data.materials.new(name=f'Material_{density}')
        mat.use_nodes = True
        cube.data.materials.append(mat)

        size = int(density * 8)
        img = Image.new('RGB', (size, size), color='white')
        texture_path = os.path.join(tmpdir, f'some_texture_{density}.png')
        img.save(texture_path)

        image = bpy.data.images.load(filepath=texture_path)
        image.pack()
        image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        image_node.image = image

        mat.node_tree.links.new(
            image_node.outputs['Color'],
            mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
        )

    return cubes


@pytest.fixture
def create_texel_density_obj_no_texture():
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'cube'
    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True
    cube.data.materials.append(mat)
    return cube


@pytest.fixture
def create_transparent_material_obj(tmpdir):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    blend_cube = bpy.context.active_object
    blend_cube.name = 'blend_cube'

    mat_blend = bpy.data.materials.new(name='Material_blend_method')
    mat_blend.blend_method = 'BLEND'
    blend_cube.data.materials.append(mat_blend)

    bpy.ops.mesh.primitive_cube_add()
    alpha_cube = bpy.context.active_object
    alpha_cube.name = 'alpha_cube'

    mat = bpy.data.materials.new(name='Material_opaque')
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE'
    alpha_cube.data.materials.append(mat)

    img = Image.new('RGB', (5, 5), color='white')
    texture_path = os.path.join(tmpdir, 'alpha_texture.png')
    img.save(texture_path)

    image = bpy.data.images.load(filepath=texture_path)
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    )

    return blend_cube, alpha_cube


@pytest.fixture
def create_objects_with_materials_and_textures(tmpdir):
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'cube'

    # MI_BB material should be ignored
    mat_mi_bb = bpy.data.materials.new(name='MI_BB')
    mat_mi_bb.use_nodes = True
    cube.data.materials.append(mat_mi_bb)

    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    plane.name = 'plane'

    mat_mi_aa = bpy.data.materials.new(name='MI_AA')
    mat_mi_aa.use_nodes = True
    plane.data.materials.append(mat_mi_aa)

    color_mi_aa = Image.new('RGB', (2048, 2048), color='white')
    color_mi_aa_path = os.path.join(tmpdir, 'MI_AA_color_texture.png')
    color_mi_aa.save(color_mi_aa_path)

    metallic_mi_aa = Image.new('RGB', (1024, 500), color='white')
    metallic_mi_aa_path = os.path.join(tmpdir, 'MI_AA_metallic_texture.png')
    metallic_mi_aa.save(metallic_mi_aa_path)

    img_mi_bb = Image.new('RGB', (2048, 2048), color='white')
    img_mi_bb_path = os.path.join(tmpdir, 'MI_BB_color_texture.png')
    img_mi_bb.save(img_mi_bb_path)

    image = bpy.data.images.load(filepath=color_mi_aa_path)
    color_node_mi_aa = mat_mi_aa.node_tree.nodes.new('ShaderNodeTexImage')
    color_node_mi_aa.image = image

    image = bpy.data.images.load(filepath=metallic_mi_aa_path)
    metallic_node_mi_aa = mat_mi_aa.node_tree.nodes.new('ShaderNodeTexImage')
    metallic_node_mi_aa.image = image

    image = bpy.data.images.load(filepath=img_mi_bb_path)
    image_node_mi_bb = mat_mi_bb.node_tree.nodes.new('ShaderNodeTexImage')
    image_node_mi_bb.image = image

    mat_mi_aa.node_tree.links.new(
        color_node_mi_aa.outputs['Color'],
        mat_mi_aa.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )
    mat_mi_aa.node_tree.links.new(
        metallic_node_mi_aa.outputs['Color'],
        mat_mi_aa.node_tree.nodes['Principled BSDF'].inputs['Metallic']
    )
    mat_mi_bb.node_tree.links.new(
        image_node_mi_bb.outputs['Color'],
        mat_mi_bb.node_tree.nodes['Principled BSDF'].inputs['Metallic']
    )

    return plane, cube


@pytest.fixture
def create_blend_materialtype_object():
    """
    Creates cube model with assigned BLEND material type
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    blend_material_object = bpy.context.active_object
    mat = bpy.data.materials.new(name="blend_mat")
    mat.blend_method = 'BLEND'
    blend_material_object.data.materials.append(mat)
    blend_material_object.name = 'blend_object'
    return blend_material_object


@pytest.fixture
def create_opaque_materialtype_object():
    """
    Creates cube model with assigned OPAQUE material type
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    opaque_material_object = bpy.context.active_object
    mat = bpy.data.materials.new(name="opaque_mat")
    mat.blend_method = 'OPAQUE'
    opaque_material_object.data.materials.append(mat)
    opaque_material_object.name = 'opaque_object'
    return opaque_material_object


@pytest.fixture
def create_opaque_materialtype_object_nodes():
    """
    Creates cube model with assigned OPAQUE material type with node tree enabled
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    opaque_material_object = bpy.context.active_object
    mat = bpy.data.materials.new(name="opaque_mat")
    mat.blend_method = 'OPAQUE'
    mat.use_nodes = True
    opaque_material_object.data.materials.append(mat)
    opaque_material_object.name = 'opaque_object'
    return opaque_material_object


@pytest.fixture
def create_opaque_blend_materialtype_scene():
    """
    Creates scene with assigned OPAQUE aand BLEND material types
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    opaque_material_object = bpy.context.active_object
    mat = bpy.data.materials.new(name="opaque_mat")
    mat.blend_method = 'OPAQUE'
    opaque_material_object.data.materials.append(mat)
    opaque_material_object.name = 'opaque_object'

    bpy.ops.mesh.primitive_cube_add()
    blend_material_object = bpy.context.active_object
    mat = bpy.data.materials.new(name="blend_mat")
    mat.blend_method = 'BLEND'
    blend_material_object.data.materials.append(mat)
    blend_material_object.name = 'blend_object'

    return opaque_material_object, blend_material_object


@pytest.fixture
def create_multimaterial_materialtype_scene():
    """
    Creates scene with assigned OPAQUE/BLEND/CLIP material types
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    multimat_object_1 = bpy.context.active_object
    opaque_mat = bpy.data.materials.new(name="opaque_mat")
    opaque_mat.blend_method = 'OPAQUE'
    blend_mat = bpy.data.materials.new(name="blend_mat")
    blend_mat.blend_method = 'BLEND'
    multimat_object_1.data.materials.append(opaque_mat)
    multimat_object_1.data.materials.append(blend_mat)
    multimat_object_1.name = 'multimat_object_1'

    bpy.ops.mesh.primitive_cube_add()
    multimat_object_2 = bpy.context.active_object
    opaque_mat = bpy.data.materials.new(name="opaque_mat")
    opaque_mat.blend_method = 'OPAQUE'
    clip_mat = bpy.data.materials.new(name="clip_mat")
    clip_mat.blend_method = 'CLIP'
    multimat_object_2.data.materials.append(opaque_mat)
    multimat_object_2.data.materials.append(clip_mat)
    multimat_object_2.name = 'multimat_object_2'

    return multimat_object_1, multimat_object_2


@pytest.fixture
def multiple_objects_two_selected():
    """
    Adds three basic cube models to the scene. First and third are selected.
    """
    reset_blender_scene()
    objects = []
    for i in range(1, 4):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = currentframe().f_code.co_name + '_{}'.format(i)
        objects.append(cube)

    objects[0].select_set(state=True)
    objects[1].select_set(state=False)
    objects[2].select_set(state=True)

    return tuple(objects)


def get_texture_paths(tmpdir, number_of_paths):
    """
    Creates given number of images in test temporary directory.
    """
    texture_paths = []
    for i in range(1, number_of_paths + 1):
        texture_path = os.path.join(tmpdir, 'texture_{}.png'.format(i))

        img = Image.new('RGB', (4, 4), color='white')
        img.save(texture_path)
        texture_paths.append(texture_path)

    return texture_paths


@pytest.fixture
def multiple_objects_with_materials_two_selected(tmpdir):
    """
    Adds three basic cube models with materials to the scene. First and third are selected.
    """
    reset_blender_scene()
    objects = []
    texture_paths = get_texture_paths(tmpdir, 6)
    it = iter(texture_paths)
    for i in range(1, 4):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = 'Cube_{}'.format(i)

        mat = bpy.data.materials.new(currentframe().f_code.co_name + '_{}'.format(i))
        cube.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes['Principled BSDF']
        nodes = mat.node_tree.nodes

        node_color = nodes.new('ShaderNodeTexImage')
        node_color.image = bpy.data.images.load(next(it))
        mat.node_tree.links.new(node_color.outputs['Color'], bsdf.inputs['Base Color'])

        node_normal_img = nodes.new('ShaderNodeTexImage')
        node_normal_img.image = bpy.data.images.load(next(it))
        node_normal = nodes.new('ShaderNodeNormalMap')
        mat.node_tree.links.new(node_normal_img.outputs['Color'], node_normal.inputs['Color'])
        mat.node_tree.links.new(node_normal.outputs['Normal'], bsdf.inputs['Normal'])

        cube.select_set(state=True)
        objects.append(cube)

    objects[0].select_set(state=True)
    objects[1].select_set(state=False)
    objects[2].select_set(state=True)

    return tuple(objects)


@pytest.fixture
def create_flipped_uv():
    """
    Adds model with multiple UV layers (flipped and regular) to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_plane_add()
    plane_flipped_uv = bpy.context.active_object
    plane_flipped_uv.name = 'plane_flipped_uv'
    plane_flipped_uv.data.uv_layers.new(name="correct_uv")

    incorrect_uv = plane_flipped_uv.data.uv_layers.new(name="flipped_uv")
    plane_flipped_uv.data.uv_layers.active = incorrect_uv

    incorrect_uv.data[0].uv.x = 2.0
    incorrect_uv.data[3].uv.x = 2.0

    plane_flipped_uv.data.uv_layers.new(name="flipped_uv_2")

    return plane_flipped_uv


@pytest.fixture
def create_overlapped_uv():
    """
    Adds two models to the scene - one with multiple UV layers
    (overlapped and regular) and one regular model.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    box_overlapped_uv = bpy.context.active_object
    box_overlapped_uv.name = 'box_overlapped_uv'

    incorrect_uv = box_overlapped_uv.data.uv_layers.new(name="overlapped_uv")
    box_overlapped_uv.data.uv_layers.active = incorrect_uv

    incorrect_uv.data[0].uv.y = 0.5
    incorrect_uv.data[1].uv.y = 0.5

    box_overlapped_uv.data.uv_layers.new(name="overlapped_uv_2")

    bpy.ops.mesh.primitive_cube_add()
    box = bpy.context.active_object
    box.name = 'box'
    return box_overlapped_uv, box


@pytest.fixture
def create_collapsed_uv():
    """
    Adds two models to the scene - one with multiple UV layers
    (collapsed and regular) and one regular model.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    box_uv = bpy.context.active_object
    box_uv.name = 'box_collapsed_uv'

    for uv_layer in box_uv.data.uv_layers:
        box_uv.data.uv_layers.remove(uv_layer)
    collapsed_uv = box_uv.data.uv_layers.new(name="collapsed_uv")
    box_uv.data.uv_layers.active = collapsed_uv

    for vert in collapsed_uv.data:
        vert.uv.x = 0.0
        vert.uv.y = 0.0

    bpy.ops.mesh.primitive_cube_add()
    box = bpy.context.active_object
    box.name = 'box'
    return box_uv, box


@pytest.fixture
def create_three_cubes_with_overlapped_uv():
    """
    Adds three models to the scene - two with overlapped UV layers
    and one without overlapped UV.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    box_overlapped_uv = bpy.context.active_object
    box_overlapped_uv.name = 'box_overlapped_uv'

    incorrect_uv = box_overlapped_uv.data.uv_layers.new(name="overlapped_uv")
    box_overlapped_uv.data.uv_layers.active = incorrect_uv

    for vert in box_overlapped_uv.data.uv_layers[0].data:
        vert.uv.y += 0.25
        vert.uv.x += 0.25

    bpy.ops.mesh.primitive_cube_add()
    box = bpy.context.active_object
    box.name = 'box'

    bpy.ops.mesh.primitive_cube_add()
    box_moved_uv = bpy.context.active_object
    box_moved_uv.name = 'box_moved_uv'

    for vert in box_moved_uv.data.uv_layers[0].data:
        vert.uv.y += 1.0
        vert.uv.x += 1.0

    return box_overlapped_uv, box, box_moved_uv


@pytest.fixture
def create_two_cubes_with_overlapped_uv_by_material():
    """
    Adds 2 cubes to the scene - with overlapped UV layers on the same material.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    box_a = bpy.context.active_object
    box_a.name = 'box_a'
    a_uv = box_a.data.uv_layers.new(name='a_uv')
    box_a.data.uv_layers.active = a_uv

    bpy.ops.mesh.primitive_cube_add()
    box_b = bpy.context.active_object
    box_b.name = 'box_b'
    box_b.data.uv_layers.new(name='b_uv')

    mat_ab = bpy.data.materials.new('ab_material')
    box_a.data.materials.append(mat_ab)
    box_b.data.materials.append(mat_ab)

    return box_a, box_b


@pytest.fixture
def create_two_cubes_with_overlapped_uv_but_different_materials():
    """
    Adds 2 cubes to the scene - with overlapped UV layers, but on different materials.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    box_a = bpy.context.active_object
    box_a.name = 'box_a'
    a_uv = box_a.data.uv_layers.new(name='a_uv')
    box_a.data.uv_layers.active = a_uv

    bpy.ops.mesh.primitive_cube_add()
    box_b = bpy.context.active_object
    box_b.name = 'box_b'
    box_b.data.uv_layers.new(name='b_uv')

    mat_a = bpy.data.materials.new('a_material')
    mat_b = bpy.data.materials.new('b_material')
    box_a.data.materials.append(mat_a)
    box_b.data.materials.append(mat_b)

    return box_a, box_b


@pytest.fixture
def objects_with_materials(tmpdir: pytest.fixture, request: pytest.fixture):
    """
    Adds basic cubes with materials to the scene.
    Material names and quantity is configured according to fixture parameters.
    """
    reset_blender_scene()
    objects = []
    for object_id, materials in enumerate(request.param, start=1):
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = 'Cube_{}'.format(object_id)
        for material_name in materials:
            mat = bpy.data.materials.new(material_name)
            cube.data.materials.append(mat)

        objects.append(cube)

    return tuple(objects)


@pytest.fixture
def textures_with_names(tmpdir: pytest.fixture, request: pytest.fixture) -> list[str]:
    """
    Create basic images with provided names.
    """
    texture_paths = []
    for texture_name in request.param:
        texture_path = os.path.join(tmpdir, texture_name)

        img = Image.new('RGB', (5, 5), color='white')
        img.save(texture_path)
        texture_paths.append(str(texture_path))

    return texture_paths


@pytest.fixture
def non_reseted_transform_scene():
    """
    Add translated, rotated, scaled Suzanne's heads to the scene.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_monkey_add()
    t_monkey = bpy.context.active_object
    t_monkey.name = 't_suzanne'
    t_monkey.matrix_world @= Matrix.Translation((0.002, 0.4, -2.0))

    bpy.ops.mesh.primitive_monkey_add()
    r_monkey = bpy.context.active_object
    r_monkey.name = 'r_suzanne'
    r_monkey.matrix_world @= Matrix.Rotation(radians(45), 4, (0.0, 0.0, 1.0))

    bpy.ops.mesh.primitive_monkey_add()
    s_monkey = bpy.context.active_object
    s_monkey.matrix_world @= Matrix.Scale(0.9, 4, (1.0, 0.0, 0.0))
    s_monkey.name = 's_suzanne'

    return t_monkey, r_monkey, s_monkey


@pytest.fixture
def rotated_model():
    """
    Add rotated Suzanne's heads to the scene.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_monkey_add()
    r_monkey = bpy.context.active_object
    r_monkey.name = 'r_suzanne'
    r_monkey.matrix_world @= Matrix.Rotation(radians(90), 4, (1.0, 0.0, 0.0))

    return r_monkey


@pytest.fixture
def non_reseted_transforms_linked_duplicates():
    """
    Add linked duplicate with non-reseted transforms of Suzanne's heads to the scene.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_monkey_add()
    monkey_01 = bpy.context.active_object
    bpy.ops.object.duplicate({'object': monkey_01}, linked=True)
    monkey_02 = bpy.context.active_object
    monkey_02.matrix_world @= Matrix.Translation((2.0, 0.0, 0.0))
    return monkey_01, monkey_02


@pytest.fixture
def box_with_open_edges():
    """
    Create qube with open edges.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    open_edges_cube = bpy.context.active_object
    open_edges_cube.name = 'cube_open_edges'
    bm = bmesh.new()
    bm.from_mesh(open_edges_cube.data)
    bmesh.ops.split_edges(bm, edges=bm.edges[:2])

    bm.to_mesh(open_edges_cube.data)
    bm.free()

    return open_edges_cube


@pytest.fixture
def mesh_with_isolated_vertex():
    """
    Create mesh with isolated vertex.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    mesh_with_isolated_vertex = bpy.context.active_object
    mesh_with_isolated_vertex.name = 'mesh_with_isolated_vertex'
    bm = bmesh.new()
    bm.from_mesh(mesh_with_isolated_vertex.data)
    bmesh.ops.delete(bm, geom=bm.edges[1:3], context='EDGES')
    bmesh.ops.delete(bm, geom=bm.verts[5:6], context='VERTS')

    bm.to_mesh(mesh_with_isolated_vertex.data)
    bm.free()

    return mesh_with_isolated_vertex


@pytest.fixture
def create_objects_with_materials():
    """
    Create three objects, two with this same material
    for witch UV will overlap and control one.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'cube_overlapped_material_uv'

    mat_mi_bb = bpy.data.materials.new(name='MI_BB')
    mat_mi_bb.use_nodes = True
    cube.data.materials.append(mat_mi_bb)

    bpy.ops.mesh.primitive_plane_add()
    plane_overlapped_material_uv = bpy.context.active_object
    plane_overlapped_material_uv.name = 'plane_overlapped_material_uv'
    plane_overlapped_material_uv.data.materials.append(mat_mi_bb)

    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    plane.name = 'plane'

    mat_mi_aa = bpy.data.materials.new(name='MI_AA')
    mat_mi_aa.use_nodes = True
    plane.data.materials.append(mat_mi_aa)

    return cube, plane_overlapped_material_uv, plane


@pytest.fixture
def mesh_with_two_overlapping_faces():
    """
    Creates mesh with two overlapping faces.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(plane.data)
    bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((0.5, 0.5, 0.0)))
    bm.to_mesh(plane.data)
    bm.free()


@pytest.fixture
def mesh_with_overlapping_face():
    """
    Create mesh with overlapped face and control cube.
    """
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.mesh.primitive_cube_add()
    overlapped_faces = bpy.context.active_object
    overlapped_faces.name = 'overlapping_face'
    bm = bmesh.new()
    bm.from_mesh(overlapped_faces.data)
    bmesh.ops.create_grid(bm, size=0.5, matrix=Matrix.Translation((0.0, 0.0, 1.0)))
    bm.to_mesh(overlapped_faces.data)
    bm.free()

    return mesh_with_isolated_vertex


@pytest.fixture
def plane_with_overlapping_face():
    """
    Create plane with an overlapped face and a non-overlapped face.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_plane_add()
    plane = bpy.context.active_object
    plane.name = 'plane'

    mesh = plane.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces)

    bm.faces.ensure_lookup_table()
    bmesh.ops.split(bm, geom=[bm.faces[0]])

    bm.faces.ensure_lookup_table()
    bmesh.ops.rotate(
        bm,
        verts=bm.faces[0].verts,
        cent=(0.0, 1.0, 0.0),
        matrix=Matrix.Rotation(radians(45.0), 3, 'Z')
    )

    bm.faces.ensure_lookup_table()
    bmesh.ops.translate(
        bm,
        verts=bm.faces[0].verts,
        vec=(-1.0, -0.5, 0.0)
    )

    bm.faces.ensure_lookup_table()
    duplicate = bmesh.ops.duplicate(
        bm,
        geom=[bm.faces[0]]
    )
    verts_dupe = [
        element for element in duplicate['geom']
        if isinstance(element, bmesh.types.BMVert)
    ]

    bmesh.ops.translate(
        bm,
        verts=verts_dupe,
        vec=(0.0, 2.0, 0.0)
    )

    bm.to_mesh(mesh)
    bm.free()

    return plane


@pytest.fixture
def create_basic_cube_cm():
    """
    Adds basic cube to the scene, setup displayed unit as 'CENTIMETERS' and unit scale as '0.01'.
    """
    reset_blender_scene()
    bpy.context.scene.unit_settings.length_unit = 'CENTIMETERS'
    bpy.context.scene.unit_settings.scale_length = 0.01
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'basic_cube'

    return cube


@pytest.fixture
def object_with_triangles():
    """
    Create two object one triangulated.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cylinder_add()
    cylinder = bpy.context.active_object
    cylinder.name = 'cylinder'

    bpy.ops.mesh.primitive_cylinder_add()
    cylinder_tris = bpy.context.active_object
    cylinder_tris.name = 'cylinder_tris'

    mesh = cylinder_tris.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()

    return cylinder, cylinder_tris


@pytest.fixture
def light_meshes_empties_cameras():
    """
    Create lights, meshes, empties and cameras.
    """
    reset_blender_scene()

    bpy.ops.mesh.primitive_cube_add()
    cube00 = bpy.context.active_object
    cube00.name = 'cube00'

    bpy.ops.mesh.primitive_cube_add()
    cube01 = bpy.context.active_object
    cube01.name = 'cube01'

    bpy.ops.object.empty_add()
    empty00 = bpy.context.active_object
    empty00.name = 'empty00'

    bpy.ops.object.empty_add()
    empty01 = bpy.context.active_object
    empty01.name = 'empty01'

    bpy.ops.object.light_add()
    light00 = bpy.context.active_object
    light00.name = 'light00'

    bpy.ops.object.light_add()
    light01 = bpy.context.active_object
    light01.name = 'light01'

    bpy.ops.object.camera_add()
    cam00 = bpy.context.active_object
    cam00.name = 'cam00'

    bpy.ops.object.camera_add()
    cam01 = bpy.context.active_object
    cam01.name = 'cam01'

    bpy.ops.curve.primitive_bezier_curve_add()
    curve00 = bpy.context.active_object
    curve00.name = 'curve00'

    bpy.ops.curve.primitive_bezier_curve_add()
    curve01 = bpy.context.active_object
    curve01.name = 'curve01'

    bpy.ops.surface.primitive_nurbs_surface_curve_add()
    surface00 = bpy.context.active_object
    surface00.name = 'surface00'

    bpy.ops.surface.primitive_nurbs_surface_curve_add()
    surface01 = bpy.context.active_object
    surface01.name = 'surface01'

    bpy.ops.object.metaball_add()
    metaball00 = bpy.context.active_object
    metaball00.name = 'metaball00'

    bpy.ops.object.metaball_add()
    metaball01 = bpy.context.active_object
    metaball01.name = 'metaball01'

    bpy.ops.object.armature_add()
    armature00 = bpy.context.active_object
    armature00.name = 'armature00'

    bpy.ops.object.armature_add()
    armature01 = bpy.context.active_object
    armature01.name = 'armature01'

    bpy.ops.object.text_add()
    text00 = bpy.context.active_object
    text00.name = 'text00'

    bpy.ops.object.text_add()
    text01 = bpy.context.active_object
    text01.name = 'text01'

    return (
        cube00, cube01, empty00, empty01, light00, light01, cam00, cam01,
        curve00, curve01, surface00, surface01, metaball00, metaball01,
        armature00, armature01, text00, text01
    )


@pytest.fixture
def create_hidden_objects():
    """
    Adds objects hidden in various ways
    """
    reset_blender_scene()
    objects: List[bpy.types.Object] = []

    bpy.ops.mesh.primitive_monkey_add()
    hidden_view = bpy.context.active_object
    objects.append(hidden_view)
    hidden_view.name = 'monkey_hidden_in_viewport'
    hidden_view.hide_viewport = True

    bpy.ops.mesh.primitive_cube_add()
    hidden_render = bpy.context.active_object
    objects.append(hidden_render)
    hidden_render.name = 'cube_hidden_in_render'
    hidden_render.hide_render = True

    bpy.ops.mesh.primitive_cube_add()
    unselectable = bpy.context.active_object
    objects.append(unselectable)
    unselectable.name = 'cube_unselectable'
    unselectable.hide_select = True

    bpy.ops.mesh.primitive_cube_add()
    hidden_geo = bpy.context.active_object
    objects.append(hidden_geo)
    hidden_geo.name = 'cube_hidden_geometry'
    for f in hidden_geo.data.polygons:
        f.hide = True
    for v in hidden_geo.data.vertices:
        v.hide = True
    for e in hidden_geo.data.edges:
        e.hide = True
    hidden_geo.data.update()

    bpy.ops.mesh.primitive_cube_add()
    masked_vgroup = bpy.context.active_object
    objects.append(masked_vgroup)
    masked_vgroup.name = 'cube_hidden_vertex_group'
    group = masked_vgroup.vertex_groups.new(name='hide_this')
    group.add(range(len(masked_vgroup.data.vertices)), 1.0, 'ADD')
    mask: bpy.types.MaskModifier = masked_vgroup.modifiers.new('mask', 'MASK')
    mask.vertex_group = group.name
    mask.invert_vertex_group = True
    masked_vgroup.data.update()

    for obj in objects:
        obj.select_set(state=False)

    bpy.context.view_layer.update()

    return objects


@pytest.fixture
def create_merged_cubes_with_overlapped_uvs():
    """
    Adds two cubes to the scene - and merges them
    """
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.mesh.primitive_cube_add()
    box_overlapped_uv = bpy.context.active_object
    box_overlapped_uv.name = 'box_overlapped_uv'

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.join()

    return box_overlapped_uv


@pytest.fixture
def create_cube_with_material_and_not_existing_file_assigned_to_it(tmpdir: pytest.fixture):
    """
    Add a cube with an assigned material and texture
    and removes the texture after assignment
    """
    cubes = []
    reset_blender_scene()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cubes.append(cube)
    cube.name = 'cube'

    mat = bpy.data.materials.new(name='Material_name')
    mat.use_nodes = True
    cube.data.materials.append(mat)

    img = Image.new('RGB', (1, 1), color='white')
    texture_path = os.path.join(tmpdir, 'some_texture.png')
    img.save(texture_path)

    image = bpy.data.images.load(filepath=texture_path)
    image.pack()
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.image = image

    os.remove(texture_path)

    mat.node_tree.links.new(
        image_node.outputs['Color'],
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color']
    )

    return cubes
