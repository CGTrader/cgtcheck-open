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
All tests running on different edge cases
"""
import time

import pytest

import cgtcheck
import cgtcheck.blender.all_checks  # noqa F401 # this is necessary for checks to be registered
from cgtcheck.common import Properties


def run_all_checks():
    time_started = time.time()
    runner = cgtcheck.runners.CheckRunner(checks_spec={})
    for check in runner.checks:
        check.params['enabled'] = True
    runner.runall()
    time_taken = time.time() - time_started
    if time_taken > 10:
        pytest.fail('Took more than 10 seconds (%.3f seconds) to run.' % time_taken)


def test_empty_scene(create_empty_scene):
    run_all_checks()


def test_no_uv_channels(create_no_uv_cube):
    run_all_checks()


def test_no_uv_multimat_cube(create_no_uv_multimat_cube):
    run_all_checks()


def test_multiple_uv(create_two_uv_cube):
    run_all_checks()


def test_no_textures(create_no_texture_obj):
    run_all_checks()


def test_no_textures_file(create_cube_with_material_and_not_existing_file_assigned_to_it):
    run_all_checks()


def test_multiple_material_obj(create_multiple_material_object):
    run_all_checks()


def test_empty_geo_obj(create_empty_geo_obj):
    run_all_checks()


def test_one_empty_geo_obj_one_normal_obj(create_one_empty_geo_obj_one_normal_obj):
    run_all_checks()


def test_one_vertex_obj(create_one_vertex_obj):
    run_all_checks()


def test_subdivided_monkey(create_subdivided_monkey_head):
    run_all_checks()


def test_cube_hierarchy(create_cube_hierarchy):
    run_all_checks()


def test_cube_moved(create_cube_moved):
    run_all_checks()


def test_cube_rotated(create_cube_rotated):
    run_all_checks()


def test_cube_scaled(create_cube_scaled):
    run_all_checks()


def test_non_uniform_scale(create_non_uniform_scaled_cube):
    run_all_checks()


def test_hidden_objects(create_hidden_objects):
    run_all_checks()


def test_checks_implement_properties_interface():
    for check_class in cgtcheck.runners.CheckRunner._check_classes:
        assert issubclass(check_class, Properties)
