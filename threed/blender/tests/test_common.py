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

import logging

import bpy

from ..common import flip_all_objects


logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFlipModels:

    def test_cubes_are_flipped_correctly(
        self,
        create_hierarchy_of_stacked_cubes
    ):
        bottom_cube, middle_cube, top_cube = (
            bpy.data.objects['bottom_cube'],
            bpy.data.objects['middle_cube'],
            bpy.data.objects['top_cube']
        )
        flip_all_objects()
        assert bottom_cube.matrix_world.translation[2] == -1.0
        assert middle_cube.matrix_world.translation[2] == -2.75
        assert top_cube.matrix_world.translation[2] == -4.0
