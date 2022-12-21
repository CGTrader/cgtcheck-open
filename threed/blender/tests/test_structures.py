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
import logging
import cProfile
import pstats
import io

import bmesh
from mathutils import Vector

from ..structures import FaceGrid


logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFaceGrid:

    def test_cube_face_grid_faces_at_correct_boxes(
        self,
        create_basic_cube,
    ):
        divs = 5
        face_grid = FaceGrid(create_basic_cube, divisions=(5, 5, 5))
        faces_per_non_empty_box = face_grid.faces_per_non_empty_box()

        expected_face_ids = {
            0: [
                x + y * divs + z * divs * divs
                for z in range(0, divs)
                for y in range(0, divs)
                for x in range(0, 1)
            ],
            1: [
                x + y * divs + z * divs * divs
                for z in range(0, divs)
                for y in range(divs - 1, divs)
                for x in range(0, divs)
            ],
            2: [
                x + y * divs + z * divs * divs
                for z in range(0, divs)
                for y in range(0, divs)
                for x in range(divs - 1, divs)
            ],
            3: [
                x + y * divs + z * divs * divs
                for z in range(0, divs)
                for y in range(0, 1)
                for x in range(0, divs)
            ],
            4: [
                x + y * divs + z * divs * divs
                for z in range(0, 1)
                for y in range(0, divs)
                for x in range(0, divs)
            ],
            5: [
                x + y * divs + z * divs * divs
                for z in range(divs - 1, divs)
                for y in range(0, divs)
                for x in range(0, divs)
            ],
        }

        for face, expected_box_ids in expected_face_ids.items():
            for box_i in expected_box_ids:
                assert face in faces_per_non_empty_box[box_i]

        expected_faces_per_non_empty_box = {}
        for face, expected_box_ids in expected_face_ids.items():
            for box_i in expected_box_ids:
                expected_faces_per_non_empty_box.setdefault(box_i, []).append(face)

        assert faces_per_non_empty_box == expected_faces_per_non_empty_box

        expected_face_bb_size = {
            0: (Vector((-1, -1, -1)), Vector((-0.6, 1, 1))),
            1: (Vector((-1, 0.6, -1)), Vector((1, 1, 1))),
            2: (Vector((0.6, -1, -1)), Vector((1, 1, 1))),
            3: (Vector((-1, -1, -1)), Vector((1, -0.6, 1))),
            4: (Vector((-1, -1, -1)), Vector((1, 1, -0.6))),
            5: (Vector((-1, -1, 0.6)), Vector((1, 1, 1))),
        }

        for face, expected_box_ids in expected_face_ids.items():
            if face >= len(expected_face_bb_size):
                break
            exp_bb_min, exp_bb_max = expected_face_bb_size[face]
            for box_i in expected_box_ids:
                bb_min, bb_max = face_grid.bounding_boxes[box_i]
                assert bb_min.x >= (exp_bb_min.x - 1e-6)
                assert bb_min.y >= (exp_bb_min.y - 1e-6)
                assert bb_min.z >= (exp_bb_min.z - 1e-6)
                assert bb_max.x <= (exp_bb_max.x + 1e-6)
                assert bb_max.y <= (exp_bb_max.y + 1e-6)
                assert bb_max.z <= (exp_bb_max.z + 1e-6)

    def test_relevant_box_ids(
        self,
        create_basic_cube
    ):
        divs = 3
        face_grid = FaceGrid(create_basic_cube, divisions=(3, 3, 3))
        all = list(face_grid.relevant_box_ids(Vector((-1, -1, -1)), Vector((1, 1, 1))))
        assert len(all) == divs ** 3
        bottom = list(face_grid.relevant_box_ids(Vector((-1, -1, -1)), Vector((1, 1, -1))))
        assert all == list(range(divs ** 3))

        assert len(bottom) == divs ** 2
        assert bottom == [
            x + y * divs + z * divs * divs
            for z in range(0, 1)
            for y in range(0, divs)
            for x in range(0, divs)
        ]

        top = list(face_grid.relevant_box_ids(Vector((-1, -1, 1)), Vector((1, 1, 1))))
        assert len(top) == divs ** 2
        assert top == [
            x + y * divs + z * divs * divs
            for z in range(divs - 1, divs)
            for y in range(0, divs)
            for x in range(0, divs)
        ]

        x_pos = list(face_grid.relevant_box_ids(Vector((1, -1, -1)), Vector((1, 1, 1))))
        assert len(x_pos) == divs ** 2
        assert x_pos == [
            x + y * divs + z * divs * divs
            for z in range(0, divs)
            for y in range(0, divs)
            for x in range(divs - 1, divs)
        ]

        x_neg = list(face_grid.relevant_box_ids(Vector((-1, -1, -1)), Vector((-1, 1, 1))))
        assert len(x_neg) == divs ** 2
        assert x_neg == [
            x + y * divs + z * divs * divs
            for z in range(0, divs)
            for y in range(0, divs)
            for x in range(0, 1)
        ]

        y_pos = list(face_grid.relevant_box_ids(Vector((-1, 1, -1)), Vector((1, 1, 1))))
        assert len(y_pos) == divs ** 2
        assert y_pos == [
            x + y * divs + z * divs * divs
            for z in range(0, divs)
            for y in range(divs - 1, divs)
            for x in range(0, divs)
        ]

        y_neg = list(face_grid.relevant_box_ids(Vector((-1, -1, -1)), Vector((1, -1, 1))))
        assert len(y_neg) == divs ** 2
        assert y_neg == [
            x + y * divs + z * divs * divs
            for z in range(0, divs)
            for y in range(0, 1)
            for x in range(0, divs)
        ]

    def test_visualize_boxes_for_cube(
        self,
        create_basic_cube
    ):
        face_grid = FaceGrid(create_basic_cube, divisions=(5, 5, 5))
        assert len(face_grid.visualize_boxes()) == 98

    def test_subdivided_monkey_build_performance(
        self,
        create_monkey_head
    ):
        obj = create_monkey_head

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=10, use_grid_fill=True)
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()

        logger.info(f'Faces: {len(obj.data.polygons)}')

        profile = cProfile.Profile()
        profile.enable()

        FaceGrid(create_monkey_head, divisions=(10, 10, 10))

        profile.disable()

        filename = 'test_subdivided_monkey_calc_time.prof'
        profile.dump_stats(filename)
        s = io.StringIO()
        pstat = pstats.Stats(filename, stream=s)
        pstat.sort_stats('time').print_stats(20)
        logger.info(s.getvalue())
        try:
            assert pstat.total_tt < 5
        except Exception:
            logger.warning(
                f'File {filename} was not deleted, '
                'it contains profiling for failed performance test'
            )
            raise
        else:
            os.remove(filename)

    def test_subdivided_monkey_iterate_performance(
        self,
        create_monkey_head
    ):
        obj = create_monkey_head

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=10, use_grid_fill=True)
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()

        logger.info(f'Faces: {len(obj.data.polygons)}')
        grid = FaceGrid(create_monkey_head, divisions=(10, 10, 10))

        profile = cProfile.Profile()
        profile.enable()

        center_sums = Vector()
        num_faces = 0
        for faces in grid.faces_per_non_empty_box().values():
            num_faces += len(faces)
            for f in faces:
                center_sums += obj.data.polygons[f].center

        profile.disable()
        logger.info(f'{num_faces} faces read, center {center_sums / num_faces}')
        filename = 'test_subdivided_monkey_iterate_performance.prof'
        profile.dump_stats(filename)
        s = io.StringIO()
        pstat = pstats.Stats(filename, stream=s)
        pstat.sort_stats('time').print_stats(20)
        logger.info(s.getvalue())

        try:
            assert pstat.total_tt < 0.1
        except Exception:
            logger.warning(
                f'File {filename} was not deleted, '
                'it contains profiling for failed performance test'
            )
            raise
        else:
            os.remove(filename)
