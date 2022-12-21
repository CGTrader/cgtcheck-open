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
from copy import deepcopy

import pytest
from math import radians

import bpy
import bmesh
from mathutils import Vector, Matrix

import cgtcheck.blender.other_checks
from cgtcheck.blender.tests.common_blender import reset_blender_scene


logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

checks_keys = cgtcheck.metadata.checks.keys()
params_disabled = {'enabled': False}
checks_spec_disabled = {key: params_disabled for key in checks_keys}


class FakeFaceGrid:
    def __init__(self, obj):
        self.faces_per_box = [[0, 1]]


class FakeFaceGridFacesInMultipleBoxes:
    def __init__(self, obj):
        self.faces_per_box = [[0, 1], [1, 0], [0, 1]]


class FakeFaceGridOneFaceInBox:
    def __init__(self, obj):
        self.faces_per_box = [[0], [1]]


class TestOverlappingFaces:

    _check_key = 'overlappingFaces'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'warning',
    }

    def assert_overlapping_faces(self, runner, overlapping_faces):
        assert runner.format_reports()[0]['items'][0]['overlapping_faces'] == overlapping_faces

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_overlapping_faces_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()

        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapping_faces': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapping_face_on_plane_failed(
        self,
        plane_with_overlapping_face,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Object contains overlapping faces',
            'identifier': self._check_key,
            'msg_type': 'warning',
            'items': [{
                'item': 'plane',
                'message': 'Object "{item}" contains overlapping faces with the following IDs: '
                           '{overlapping_faces}',
                'overlapping_faces': '"(1, 2)"'
            }]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()

        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapping_faces': [(1, 2)]
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapping_face_on_cube_failed(
        self,
        mesh_with_overlapping_face,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Object contains overlapping faces',
            'identifier': self._check_key,
            'msg_type': 'warning',
            'items': [{
                'item': 'overlapping_face',
                'message': 'Object "{item}" contains overlapping faces with the following IDs: '
                           '{overlapping_faces}',
                'overlapping_faces': '"(5, 6)"'
            }]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()

        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapping_faces': []
                },
                {
                    'id': 1,
                    'overlapping_faces': [(5, 6)]
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_two_overlapping_faces_in_multiple_grid_boxes(
        self,
        runner: cgtcheck.runners.CheckRunner,
        mesh_with_two_overlapping_faces,
        mocker,
    ):
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGridFacesInMultipleBoxes)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_two_overlapping_faces_not_in_same_grid_box(
        self,
        runner: cgtcheck.runners.CheckRunner,
        mesh_with_two_overlapping_faces,
        mocker,
    ):
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGridOneFaceInBox)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_basic_overlapping_faces(
        self,
        runner: cgtcheck.runners.CheckRunner,
        mesh_with_two_overlapping_faces,
        mocker,
    ):
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_non_parallel_faces_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1)
        bm.faces.ensure_lookup_table()
        bmesh.ops.rotate(
            bm,
            verts=bm.faces[0].verts,
            cent=(0.0, 1.0, 0.0),
            matrix=Matrix.Rotation(radians(45.0), 3, 'X')
        )
        bm.to_mesh(plane.data)
        bm.free()
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_parallel_faces_further_than_threshold_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((0.0, 0.0, 1.0)))
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_parallel_faces_one_flipped_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1)
        bm.faces.ensure_lookup_table()
        bmesh.ops.reverse_faces(bm, faces=[bm.faces[0]])
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_two_faces_in_exact_same_place_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1)
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_one_face_within_the_other_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=0.5)
        bm.to_mesh(plane.data)
        bm.free()
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_faces_with_fully_overlapping_edge_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((2.0, 0.0, 0.0)))
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_faces_with_common_edge_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bm.edges.ensure_lookup_table()
        bmesh.ops.subdivide_edges(bm, edges=[bm.edges[0], bm.edges[2]], cuts=1)
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_face_vertex_on_edge_of_another_face_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((3.0, 0.0, 0.0)))
        bm.verts.ensure_lookup_table()
        bm.verts[4].co = Vector((1.0, 0.0, 0.0))

        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_that_two_faces_overlapping_on_almost_all_axes_are_not_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((3.0, 0.0, 0.0)))
        bm.verts.ensure_lookup_table()
        bm.verts[4].co = Vector((1.01, -1.0, 0.0))
        bm.verts[3].co = Vector((1.99, 1.0, 0.0))

        bm.to_mesh(plane.data)
        bm.free()
        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_complex_rotated_faces_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((1.0, 1.0, 0.0)))
        bm.verts.ensure_lookup_table()
        coordinates = [
            Vector((-2.1210, -1.4819, 0.0000)),
            Vector((-0.1210, -1.4819, 0.0000)),
            Vector((-2.1210, 0.5181, 0.0000)),
            Vector((1.7127, 2.2814, 0.0000)),
            Vector((2.1231, -1.0000, 0.0000)),
            Vector((4.1231, -1.0000, 0.0000)),
            Vector((0.0998, 2.1660, 0.0000)),
            Vector((4.1231, 1.0000, 0.0000)),
        ]
        for v, coord in zip(bm.verts, coordinates):
            v.co = coord

        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=(0.0, 1.0, 0.0),
            matrix=Matrix((
                (0.15, -0.6, 0.82),
                (0.34, 0.81, -0.57),
                (0.21, 0.57, 0.81)
            ))
        )
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_almost_parallel_faces_partially_within_distance_threshold_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((0, 0, 0.0009)))
        bm.faces.ensure_lookup_table()

        bmesh.ops.rotate(
            bm,
            verts=bm.faces[1].verts,
            cent=(0.0, 1.0, 0.0),
            matrix=Matrix.Rotation(radians(0.5), 3, 'X')
        )
        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_parallel_faces_far_from_origin_overlapping(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((0, 0, 0.0009)))
        bm.to_mesh(plane.data)
        bm.free()
        plane.location = 10, 10, 10
        plane.rotation_euler = 0, 1, 1

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is False
        self.assert_overlapping_faces(runner, '"(0, 1)"')

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_faces_overlapp_beyond_the_threshold(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        mocker,
    ):
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        bm = bmesh.new()
        bm.from_mesh(plane.data)
        bmesh.ops.create_grid(bm, size=1, matrix=Matrix.Translation((1.0, 1.0, 0.0)))
        bm.verts.ensure_lookup_table()
        coordinates = [
            Vector((-37.33009338378906, -64.80783081054688, 107.83377838134766)),
            Vector((-36.354942321777344, -64.49017333984375, 107.85337829589844)),
            Vector((-36.64208221435547, -48.735233306884766, 108.82661437988281)),
            Vector((-37.80107116699219, -50.03873062133789, 108.74608612060547)),
            Vector((-36.64208221435547, -48.735233306884766, 108.82661437988281)),
            Vector((-36.80851745605469, -45.514225006103516, 109.02558135986328)),
            Vector((-37.922569274902344, -47.981388092041016, 108.8731689453125)),
            Vector((-37.80107116699219, -50.03873062133789, 108.74608612060547)),
        ]
        for v, coord in zip(bm.verts, coordinates):
            v.co = coord

        bm.to_mesh(plane.data)
        bm.free()

        mocker.patch('cgtcheck.blender.geometry_checks.FaceGrid', FakeFaceGrid)

        runner.runall()
        assert runner.passed is True


class TestDccTrianglesRatio:
    check_key = 'dccTrianglesRatio'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_dcc_triangles_ration_success(self, object_with_triangles):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'comparator': '>',
                'threshold': '0.785',
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.check_key
        ).format_properties()
        assert properties == {'trianglesRatio': '0.785'}

    def test_dcc_triangles_ration_failed(self, object_with_triangles):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'comparator': '>',
                'threshold': '0.12',
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Triangle ratio requirements is not fulfilled',
            'identifier': self.check_key,
            'msg_type': 'error',
            'items': [{
                u'message': u'Triangle ratio {found} for models in scene is {comparator} '
                            u'than the threshold: {expected}',
                u'expected': '0.120',
                u'comparator': '>',
                u'found': '0.785',
            }]
        }]
        properties = next(
            check for check in runner.checks if check.key == self.check_key
        ).format_properties()
        assert properties == {'trianglesRatio': '0.785'}


class TestFacetedGeometry:
    check_key = 'facetedGeometry'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[check_key] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_faceted_geometry_success(
        self,
        create_no_faceted_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'faceted': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_smooth_normals_success(
        self,
        create_smooth_normals_monkey_head,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'faceted': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_faceted_geometry_failed(
        self,
        create_basic_cube_and_monkey_head,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Fully faceted objects',
            'identifier': 'facetedGeometry',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Object "{item}" is fully faceted',
                    'item': 'basic_cube',
                    'expected': False,
                    'found': True
                },
                {
                    'message': 'Object "{item}" is fully faceted',
                    'item': 'basic_monkey',
                    'expected': False,
                    'found': True
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self.check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'faceted': True
                },
                {
                    'id': 1,
                    'faceted': True
                }
            ]
        }

        reset_blender_scene()
