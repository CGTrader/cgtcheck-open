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

import bpy
import pytest

from ..common import reset


@pytest.fixture
def create_basic_cube():
    """
    Adds basic cube model to the scene.
    """
    reset()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'basic_cube'
    return cube


@pytest.fixture
def create_monkey_head():
    """
    Adds monkey head model to the scene.
    """
    reset()
    bpy.ops.mesh.primitive_monkey_add()
    monkey = bpy.context.active_object
    monkey.name = 'basic_monkey'
    monkey.select_set(state=False)
    return monkey


@pytest.fixture
def create_basic_cube_and_monkey_head():
    """
    Adds basic cube and monkey head model to the scene.
    """
    reset()
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
def create_hard_cube():
    """
    Adds hard edged cube model to the scene.
    """
    reset()
    bpy.ops.mesh.primitive_cube_add()
    hard_cube = bpy.context.active_object
    hard_cube.name = 'hard_cube'
    for edge in hard_cube.data.edges:
        edge.use_edge_sharp = True
    for poly in hard_cube.data.polygons:
        poly.use_smooth = True
    return hard_cube


@pytest.fixture
def create_bottom_center_cube():
    """
    Adds basic cube model and move it so that its centre point
    on the bottom bounding box is in the position 0,0,0.
    """
    reset()
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = 'bottom_center_cube'
    cube.location = 0, 0, 1
    return cube


@pytest.fixture
def create_hierarchy_of_stacked_cubes():
    """
    Adds basic cube models and moves them in such a way that they're stacked upon one another.
    """
    reset()

    cubes = []

    bpy.ops.mesh.primitive_cube_add()
    bottom_cube = bpy.context.active_object
    bottom_cube.name = 'bottom_cube'
    bottom_cube.location = 0, 0, 1
    cubes.append(bottom_cube)

    bpy.ops.mesh.primitive_cube_add()
    middle_cube = bpy.context.active_object
    middle_cube.name = 'middle_cube'
    middle_cube.location = 0, 0, 2.75
    middle_cube.scale = 0.75, 0.75, 0.75
    middle_cube.parent = bottom_cube
    middle_cube.matrix_parent_inverse = bottom_cube.matrix_world.inverted()
    cubes.append(middle_cube)

    bpy.ops.mesh.primitive_cube_add()
    top_cube = bpy.context.active_object
    top_cube.name = 'top_cube'
    top_cube.location = 0, 0, 4
    top_cube.scale = 0.5, 0.5, 0.5
    top_cube.parent = middle_cube
    top_cube.matrix_parent_inverse = middle_cube.matrix_world.inverted()
    cubes.append(top_cube)

    return cubes
