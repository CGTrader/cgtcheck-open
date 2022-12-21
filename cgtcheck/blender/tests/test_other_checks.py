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
from copy import deepcopy
from typing import Tuple, List
import bpy
import pytest

import cgtcheck
import cgtcheck.blender.other_checks
from cgtcheck.blender.tests.common_blender import reset_blender_scene


logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

checks_keys = cgtcheck.metadata.checks.keys()
params_disabled = {'enabled': False}
checks_spec_disabled = {key: params_disabled for key in checks_keys}  # WARNING: same dict is reused


class TestMultiMaterial:

    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['multiMaterial'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_single_material_success(
        self,
        create_single_material_object,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'multiMaterial':
                properties = check.format_properties()

        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'materials': [0]
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_single_material_failed(
        self,
        create_multiple_material_object,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Geometry have more than one material assigned',
            'identifier': 'multiMaterial',
            'msg_type': 'warning',
            'items': [{
                'message': '"{item}"',
                'item': 'model_multiple_material',
                'expected': 1,
                'found': 2
            }]
        }]
        for check in runner.checks:
            if check.key == 'multiMaterial':
                properties = check.format_properties()

        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'materials': [0, 1]
                }
            ]
        }


class TestTextureResolutionsNotPowerOfTwo:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['textureResolutionNotPowerOf2'] = {
        'enabled': True,
        'type': 'error',
    }
    res = (6, 6)
    other_res = (8, 8)
    yet_another_res = (10, 10)
    slot_to_check_1 = 'occlusion'
    slot_to_check_2 = 'roughness'
    slot_to_check_3 = 'metallic'

    def test_not_power_of_two_empty_tex_paths_success(self):
        reset_blender_scene()
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureResolutionNotPowerOf2':
                properties = check.format_properties()
        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[other_res, other_res, other_res, other_res]], indirect=True
    )
    def test_not_power_of_two_success(
        self, textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'material_name_2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize(
        'textures_with_res', [[res, res, other_res, yet_another_res]], indirect=True
    )
    def test_not_power_of_two_failed(
        self, textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'material_name_2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Texture resolution is not a power of 2',
            'identifier': 'textureResolutionNotPowerOf2',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Texture "{item}" resolution {found} is not a power of 2, '
                               'expected a resolution like: {expected}, etc.',
                    'item': os.path.basename(tex_1),
                    'found': (6, 6),
                    'expected': (4, 4)
                },
                {
                    'message': 'Texture "{item}" resolution {found} is not a power of 2, '
                               'expected a resolution like: {expected}, etc.',
                    'item': os.path.basename(tex_2),
                    'found': (6, 6),
                    'expected': (4, 4)
                },
                {
                    'message': 'Texture "{item}" resolution {found} is not a power of 2, '
                               'expected a resolution like: {expected}, etc.',
                    'item': os.path.basename(tex_4_different_res),
                    'found': (10, 10),
                    'expected': (8, 8)
                }
            ]
        }
        ]
        for check in runner.checks:
            if check.key == 'textureResolutionNotPowerOf2':
                properties = check.format_properties()
        assert properties == {
            'texture': [
                {
                    'name': os.path.basename(tex_1),
                    'resolution': [6, 6]
                },
                {
                    'name': os.path.basename(tex_2),
                    'resolution': [6, 6]
                },
                {
                    'name': os.path.basename(tex_3_other_res),
                    'resolution': [8, 8]
                },
                {
                    'name': os.path.basename(tex_4_different_res),
                    'resolution': [10, 10]
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_not_power_of_two_texture_paths_from_collector_failed(
        self,
        create_objects_with_materials_and_textures,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Texture resolution is not a power of 2',
            'identifier': 'textureResolutionNotPowerOf2',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Texture "{item}" resolution {found} is not a power of 2, '
                               'expected a resolution like: {expected}, etc.',
                    'item': 'MI_AA_metallic_texture.png',
                    'found': (1024, 500),
                    'expected': (1024, 256)
                }
            ]
        }
        ]
        for check in runner.checks:
            if check.key == 'textureResolutionNotPowerOf2':
                properties = check.format_properties()
        assert properties == {
            'texture': [
                {
                    'name': 'MI_AA_color_texture.png',
                    'resolution': [2048, 2048]
                },
                {
                    'name': 'MI_AA_metallic_texture.png',
                    'resolution': [1024, 500]
                },
                {
                    'name': 'MI_BB_color_texture.png',
                    'resolution': [2048, 2048]
                }
            ]
        }


class TestTriangleMaxCount:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['triangleMaxCount'] = {
        'parameters': {
            'triMaxCount': 970
        },
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_triangle_max_count_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'triangleMaxCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'tri_count': 12
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_triangle_max_count_failed(
        self,
        create_basic_cube_and_monkey_head,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Scene triangle count exceeded',
            'identifier': 'triangleMaxCount',
            'msg_type': 'warning',
            'items': [
                {
                    'message': '{item} triangle count of {found} exceeds the maximum allowed: '
                               '{expected}',
                    'item': 'Model',
                    'expected': 970,
                    'found': 980
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'triangleMaxCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'tri_count': 12
                },
                {
                    'id': 1,
                    'tri_count': 968
                }
            ]
        }


class TestHardEdges:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['noHardEdges'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_hard_edges_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'noHardEdges':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'hard_edges': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_hard_edges_failed(
        self,
        create_hard_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing hard edges',
            'identifier': 'noHardEdges',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" has hard edges',
                    'item': 'hard_cube',
                    'expected': False,
                    'found': True
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'noHardEdges':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'hard_edges': True
                }
            ]
        }


class TestNoNgons:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['noNgons'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_ngons_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'noNgons':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'ngons': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_ngons_failed(
        self,
        create_ngon,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing N-gons',
            'identifier': 'noNgons',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" contains N-gons',
                    'item': 'ngon',
                    'expected': False,
                    'found': True
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'noNgons':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'ngons': True
                }
            ]
        }


class TestZeroAngleFaceCorners:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['zeroAngleFaceCorners'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_angle_face_corners_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'zeroAngleFaceCorners':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_angle_corners': 0
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_angle_face_corners_failed(
        self,
        create_zero_angle_face_corners,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing faces with zero-angle corners',
            'identifier': 'zeroAngleFaceCorners',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" has {found} faces with zero-angle corners',
                    'item': 'zero_angle_cube',
                    'expected': 0,
                    'found': 2
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'zeroAngleFaceCorners':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_angle_corners': 2
                }
            ]
        }


class TestZeroFaceArea:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['zeroFaceArea'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_face_area_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'zeroFaceArea':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_area_face': 0
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_face_area_failed(
        self,
        create_zero_angle_face_corners,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing zero-area faces',
            'identifier': 'zeroFaceArea',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" has {found} faces with zero area',
                    'item': 'zero_angle_cube',
                    'expected': 0,
                    'found': 2
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'zeroFaceArea':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_area_face': 2
                }
            ]
        }


class TestZeroLengthEdge:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['zeroLengthEdge'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_length_edge_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'zeroLengthEdge':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_length_edge': 0
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_zero_length_edge_failed(
        self,
        create_zero_length_edge,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing zero-length edges',
            'identifier': 'zeroLengthEdge',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" has {found} zero-length edges',
                    'item': 'zero_length_edge_cube',
                    'expected': 0,
                    'found': 8
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'zeroLengthEdge':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'zero_length_edge': 8
                }
            ]
        }


class TestNoUvTiling:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['noUvTiling'] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_uv_tiling_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'noUvTiling':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_inside': ['UVMap'],
                    'uv_outside': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_uv_tiling_failed(
        self,
        create_uv_outside_zero_one,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'UV tiling found in objects',
            'identifier': 'noUvTiling',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Object "{item}" has UVs outside of 0 to 1 range '
                               'in UV layer(s): {uv_layers}',
                    'item': 'uv_outside_zero_one',
                    'uv_layers': '"incorrect_uv", "incorrect_uv_2"'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'noUvTiling':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_inside': ['UVMap', 'correct_uv'],
                    'uv_outside': ['incorrect_uv', 'incorrect_uv_2']
                }
            ]
        }


class TestSingleUVChannel:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['singleUVChannel'] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_single_uv_channel_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'singleUVChannel':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_amount': 1
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_single_uv_channel_failed(
        self,
        create_uv_outside_zero_one,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Multiple or none UV channels found in objects',
            'identifier': 'singleUVChannel',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Object "{item}" has {found} UV channels',
                    'item': 'uv_outside_zero_one',
                    'expected': 0,
                    'found': 4
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'singleUVChannel':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_amount': 4
                }
            ]
        }


class TestCenteredGeometryBoundingBox:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['centeredGeometryBoundingBox'] = {
        'parameters': {
            'positionDeviation': [0.1, 0.1, 0.1]
        },
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_centered_geometry_bounding_box_success(
        self,
        create_bottom_center_position_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'centeredGeometryBoundingBox':
                properties = check.format_properties()
        assert properties == {
            'objects': {
                'bottom_center_position': (0.0, 0.0, 0.0)
            }
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_centered_geometry_bounding_box_failed(
        self,
        create_empty_scene,
        create_basic_cube_and_monkey_head,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'The bounding box of the scene geometry is not correctly centered',
            'identifier': 'centeredGeometryBoundingBox',
            'msg_type': 'warning',
            'items': []
        }]
        for check in runner.checks:
            if check.key == 'centeredGeometryBoundingBox':
                properties = check.format_properties()
        assert properties == {
            'objects': {
                'bottom_center_position': (0.0, 0.0, -1.0)
            }
        }


class TestCenteredChildPivots:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['centeredChildPivots'] = {
        'parameters': {
            'positionDeviation': 0.001
        },
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_centered_child_pivots_success(
        self,
        create_bottom_center_position_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'centeredChildPivots':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'pivot_position': (0.0, 0.0, 1.0),
                    'bb_center': (0.0, 0.0, 1.0)
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_centered_child_pivots_failed(
        self,
        create_parent_child_cubes,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Pivots are not centered in child objects',
            'identifier': 'centeredChildPivots',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object\'s "{item}" pivot {found} is not at '
                               'bounding box center: ({expected})',
                    'item': 'first_child',
                    'expected': (4.0, 2.0, 3.0),
                    'found': (0.0, 0.0, 0.0)
                },
                {
                    'message': 'Object\'s "{item}" pivot {found} is not at '
                               'bounding box center: ({expected})',
                    'item': 'second_child',
                    'expected': (0.0, 4.0, 2.0),
                    'found': (0.0, 0.0, 0.0)
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'centeredChildPivots':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'pivot_position': (0.0, 0.0, 0.0),
                    'bb_center': (4.0, 2.0, 3.0)
                },
                {
                    'id': 1,
                    'pivot_position': (0.0, 0.0, 0.0),
                    'bb_center': (0.0, 0.0, 0.0)
                },
                {
                    'id': 2,
                    'pivot_position': (0.0, 0.0, 0.0),
                    'bb_center': (0.0, 4.0, 2.0)
                }
            ]
        }


class TestTopLevelZeroPosition:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['topLevelZeroPosition'] = {
        'parameters': {
            'positionDeviation': 0.001
        },
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_top_level_zero_position_success(
        self,
        create_empty_scene,
        create_basic_cube_and_monkey_head,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'topLevelZeroPosition':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'pivot_position': (0.0, 0.0, 0.0)
                },
                {
                    'id': 1,
                    'pivot_position': (0.0, 0.0, 0.0)
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_top_level_zero_position_failed(
        self,
        create_two_cubes_not_at_origin,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Pivot point location not at world origin (0, 0, 0) for top-level objects',
            'identifier': 'topLevelZeroPosition',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object\'s "{item}" pivot {found} is not at origin ({expected})',
                    'item': 'create_bottom_center_position_cube',
                    'expected': (0, 0, 0),
                    'found': (0.0, 4.0, 2.0)
                },
                {
                    'message': 'Object\'s "{item}" pivot {found} is not at origin ({expected})',
                    'item': 'create_bottom_center_position_cube.001',
                    'expected': (0, 0, 0),
                    'found': (0.0, 0.0, 1.0)
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'topLevelZeroPosition':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'pivot_position': (0.0, 4.0, 2.0)
                },
                {
                    'id': 1,
                    'pivot_position': (0.0, 0.0, 1.0)
                }
            ]
        }


class TestTextureResolution:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['inconsistentTexResInMaterial'] = {
        'enabled': True,
    }
    res = (6, 6)
    other_res = (8, 8)
    yet_another_res = (10, 10)
    slot_to_check_1 = 'occlusion'
    slot_to_check_2 = 'roughness'
    slot_to_check_3 = 'metallic'

    def test_texture_resolution_empty_tex_paths_success(self):
        reset_blender_scene()
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'inconsistentTexResInMaterial':
                properties = check.format_properties()
        assert properties == {
            'objects': []
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[other_res, other_res, other_res, other_res]], indirect=True
    )
    def test_texture_resolution_success(
        self, create_multiple_material_object, textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'Material': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'Material2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'inconsistentTexResInMaterial':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_1.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_2.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_3.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_1.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_3.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_4.png',
                    'resolution': [8, 8]
                }
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[res, res, other_res, yet_another_res]], indirect=True
    )
    def test_texture_resolution_failed(
        self,
        create_multiple_material_object,
        textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'Material': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'Material2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Inconsistent texture resolution in material',
            'identifier': 'inconsistentTexResInMaterial',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{material}" texture\'s "{item}" '
                               'size is {found}, expected: {expected}',
                    'material': 'Material',
                    'item': 'texture_3.png',
                    'expected': (6, 6),
                    'found': (8, 8)
                },
                {
                    'message': 'Material "{material}" texture\'s "{item}" '
                               'size is {found}, expected: {expected}',
                    'material': 'Material2',
                    'item': 'texture_3.png',
                    'expected': (6, 6),
                    'found': (8, 8)
                },
                {
                    'message': 'Material "{material}" texture\'s "{item}" '
                               'size is {found}, expected: {expected}',
                    'material': 'Material2',
                    'item': 'texture_4.png',
                    'expected': (6, 6),
                    'found': (10, 10)
                }
            ]
        }
        ]
        for check in runner.checks:
            if check.key == 'inconsistentTexResInMaterial':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_2.png',
                    'resolution': [6, 6]
                },
                {
                    'id': 0,
                    'material': 0,
                    'texture_name': 'texture_3.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_3.png',
                    'resolution': [8, 8]
                },
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'texture_4.png',
                    'resolution': [10, 10]
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_texture_resolution_texture_paths_from_collector_failed(
        self,
        create_objects_with_materials_and_textures,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Inconsistent texture resolution in material',
            'identifier': 'inconsistentTexResInMaterial',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{material}" texture\'s "{item}" '
                               'size is {found}, expected: {expected}',
                    'material': 'MI_AA',
                    'item': 'MI_AA_metallic_texture.png',
                    'expected': (2048,
                                 2048),
                    'found': (1024, 500)
                }
            ]
        }
        ]
        for check in runner.checks:
            if check.key == 'inconsistentTexResInMaterial':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'material': 1,
                    'texture_name': 'MI_BB_color_texture.png',
                    'resolution': [2048, 2048]
                },
                {
                    'id': 1,
                    'material': 0,
                    'texture_name': 'MI_AA_color_texture.png',
                    'resolution': [2048, 2048]
                },
                {
                    'id': 1,
                    'material': 0,
                    'texture_name': 'MI_AA_metallic_texture.png',
                    'resolution': [1024, 500]
                }
            ]
        }


class TestRequiredTextures:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['missingRequiredTextures'] = {
        'enabled': True,
        'type': 'error',
    }
    res = (6, 6)
    other_res = (8, 8)
    yet_another_res = (10, 10)
    slot_to_check_1 = 'opacity'
    slot_to_check_2 = 'roughness'
    slot_to_check_3 = 'metallic'
    name_with_regex_symbol = 'dummy+name'
    mat = 'M_2_3'
    mat_different_suffix = 'M_2_888'
    mat_different_prefix = 'M_8_3'
    other_mat = 'M_5_123'
    mat_base = '{}_{}_BaseColor.png'.format(mat, name_with_regex_symbol)
    mat_normal = '{}_{}_Normal.png'.format(mat_different_prefix, name_with_regex_symbol)
    mismatched_texture = '{}_{}_Roughness.png'.format(mat_different_suffix, name_with_regex_symbol)
    other_mat_base = '{}_{}_BaseColor.png'.format(other_mat, name_with_regex_symbol)
    other_mat_normal = '{}_{}_Normal.png'.format(other_mat, name_with_regex_symbol)

    def test_required_textures_empty_tex_paths_success(self):
        reset_blender_scene()
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'missingRequiredTextures':
                properties = check.format_properties()
        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[other_res, other_res, other_res, other_res]], indirect=True
    )
    def test_required_textures_success(
        self,
        create_multiple_material_object,
        required_textures_dummy_file,
        textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'Material': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'Material2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            },
            'input_file': required_textures_dummy_file,
            'tex_spec': {
                'input_files': {
                    'opacity': '^M_0_{matid}_{infilename}_{matid}_Opacity.png',
                    'metallic': '^M_0_{matid}_{infilename}_{matid}_Metalness.png'
                },
                'output_files': {},
                'parsed_variables': {},
                'required_textures': [
                    'opacity', 'metallic'
                ],
                'input_directories': [],
                'predefined_variables': {
                    "matid": "0"
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'missingRequiredTextures':
                properties = check.format_properties()
        assert properties == {
            'texture': [
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Opacity.png',
                    'delivered': True
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Opacity.png',
                    'delivered': True
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                }
            ]
        }

    def test_required_no_tex_spec_no_input_file_success(
        self,
        create_objects_with_materials_and_textures
    ):
        checks_data = {}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'missingRequiredTextures':
                properties = check.format_properties()
        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[res, res, other_res, yet_another_res]], indirect=True
    )
    def test_required_textures_failed(
        self,
        required_textures_dummy_file,
        create_multiple_material_object,
        textures_with_res: pytest.fixture
    ):
        tex_1, tex_2, tex_3_other_res, tex_4_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'Material': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                },
                'Material2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_other_res,
                    self.slot_to_check_3: tex_4_different_res,
                }
            },
            'input_file': required_textures_dummy_file,
            'tex_spec': {
                'input_files': {
                    'metallic': '^M_0_{matid}_{infilename}_{matid}_Metalness.png',
                    'roughness': '^M_0_{matid}_{infilename}_{matid}_Roughness.png',
                    'occlusion': '^M_0_{matid}_{infilename}_{matid}_AO.png',
                    'normal': '^M_0_{matid}_{infilename}_{matid}_Normal.png'
                },
                'output_files': {},
                'parsed_variables': {},
                'required_textures': [
                    'metallic', 'roughness', 'occlusion', 'normal'
                ],
                'input_directories': [],
                'predefined_variables': {
                    "matid": "0"
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Missing textures',
            'identifier': 'missingRequiredTextures',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{item}',
                    'item': 'M_0_0_required_textures_0_AO.png'
                },
                {
                    'message': '{item}',
                    'item': 'M_0_0_required_textures_0_Normal.png'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'missingRequiredTextures':
                properties = check.format_properties()
        assert properties == {
            'texture': [
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Roughness.png',
                    'delivered': True
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_AO.png',
                    'delivered': False
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Normal.png',
                    'delivered': False
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Roughness.png',
                    'delivered': True
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_AO.png',
                    'delivered': False
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Normal.png',
                    'delivered': False
                }
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_res', [[res, res, other_res, yet_another_res]], indirect=True
    )
    def test_required_textures_texture_paths_from_collector_failed(
        self,
        required_textures_dummy_file,
        create_objects_with_materials_and_textures,
        textures_with_res: pytest.fixture
    ):
        checks_data = {
            'input_file': required_textures_dummy_file,
            'tex_spec': {
                'input_files': {
                    'metallic': '^M_0_{matid}_{infilename}_{matid}_Metalness.png',
                    'roughness': '^M_0_{matid}_{infilename}_{matid}_Roughness.png',
                    'occlusion': '^M_0_{matid}_{infilename}_{matid}_AO.png',
                    'normal': '^M_0_{matid}_{infilename}_{matid}_Normal.png'
                },
                'output_files': {},
                'parsed_variables': {},
                'required_textures': [
                    'metallic', 'roughness', 'occlusion', 'normal'
                ],
                "input_directories": [],
                'predefined_variables': {
                    "matid": "0"
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Missing textures',
            'identifier': 'missingRequiredTextures',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{item}',
                    'item': 'M_0_0_required_textures_0_AO.png'
                },
                {
                    'message': '{item}',
                    'item': 'M_0_0_required_textures_0_Normal.png'
                },
                {
                    'message': '{item}',
                    'item': 'M_0_0_required_textures_0_Roughness.png'
                },
            ]
        }]
        for check in runner.checks:
            if check.key == 'missingRequiredTextures':
                properties = check.format_properties()
        assert properties == {
            'texture': [
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Roughness.png',
                    'delivered': False
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_AO.png',
                    'delivered': False
                },
                {
                    'material': 0,
                    'name': 'M_0_0_required_textures_0_Normal.png',
                    'delivered': False
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Metalness.png',
                    'delivered': True
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Roughness.png',
                    'delivered': False
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_AO.png',
                    'delivered': False
                },
                {
                    'material': 1,
                    'name': 'M_0_0_required_textures_0_Normal.png',
                    'delivered': False
                }
            ]
        }

    @pytest.mark.parametrize(
        'objects_with_materials', [[[mat], [other_mat]]], indirect=True
    )
    @pytest.mark.parametrize(
        'textures_with_names',
        [[mat_base, mat_normal, mismatched_texture, other_mat_base, other_mat_normal]],
        indirect=True,
    )
    def test_properly_display_failures(self, textures_with_names, objects_with_materials, tmpdir):
        textures_specification = {
            "input_files": {
                "color": "^M_\\d_{matid}_{infilename}_BaseColor.(png)$",
                "normal": "^M_\\d_{matid}_{infilename}_Normal.(png)$",
                "roughness": "^M_\\d_{matid}_{infilename}_Roughness.(png)$",
            },
            "output_files": {},
            "parsed_variables": {
                "matid": "^M_\\d+_(\\d+)$",
            },
            "input_directories": [],
            "required_textures": [
                "color",
                "roughness",
                "normal",
            ],
            "predefined_variables": {}
        }

        tex_paths = {
            self.mat: {
                'color': os.path.join(tmpdir, self.mat_base),
                'normal': os.path.join(tmpdir, self.mat_normal)
            },
            self.other_mat: {
                'color': os.path.join(tmpdir, self.mat_base),
                'normal': os.path.join(tmpdir, self.mat_normal)
            }
        }

        checks_data = {
            'tex_paths': tex_paths,
            'input_file': os.path.join(tmpdir, '{}.fbx'.format(self.name_with_regex_symbol)),
            'tex_spec': textures_specification,
        }

        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec, checks_data=checks_data)
        runner.runall()

        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Missing textures',
            'identifier': 'missingRequiredTextures',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{item}',
                    'item': 'M_(digit)_123_{}_Roughness.png'.format(self.name_with_regex_symbol)
                },
                {
                    'message': '{item}',
                    'item': 'M_(digit)_3_{}_Roughness.png'.format(self.name_with_regex_symbol)
                },
            ]
        }]

    @pytest.mark.parametrize(
        'objects_with_materials', [[[mat]]], indirect=True
    )
    @pytest.mark.parametrize(
        'textures_with_res', [[other_res]], indirect=True
    )
    def test_skip_unparseable_material(
        self,
        required_textures_dummy_file,
        textures_with_res: pytest.fixture,
        objects_with_materials: pytest.fixture,
    ):
        tex_1 = textures_with_res[0]
        material_regex = '^M_\\d+_(\\d+)$'
        material_not_matching_regex = 'Material'
        material_matching_regex = 'M_2_3'
        checks_data = {
            'tex_paths': {
                material_not_matching_regex: {
                    self.slot_to_check_1: tex_1,
                },
                material_matching_regex: {
                    self.slot_to_check_1: tex_1,
                }
            },
            'input_file': required_textures_dummy_file,
            'tex_spec': {
                'input_files': {
                    'opacity': '^M_0_{matid}_{infilename}_Opacity.png',
                    'metallic': '^M_0_{matid}_{infilename}_Metalness.png'
                },
                'output_files': {},
                'parsed_variables': {"matid": material_regex},
                'required_textures': [
                    'opacity', 'metallic'
                ],
                'input_directories': [],
                'predefined_variables': {},
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Missing textures',
            'identifier': 'missingRequiredTextures',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{item}',
                    'item': 'M_0_3_required_textures_Metalness.png'
                },
            ]
        }]


class TestEmbeddedTexturesFbx:
    _check_key = 'embeddedTexturesFbx'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_embedded_textures_success(
        self,
        create_texture_obj,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'textures': [
                {
                    'id': 0,
                    'is_embedded': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_embedded_textures_failed(
        self,
        create_embedded_texture_obj,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'FBX file contains embedded textures',
            'identifier': self._check_key,
            'msg_type': 'error',
            'items': [
                {
                    'message': '"{item}"',
                    'item': 'embedded_texture.png'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'textures': [
                {
                    'id': 0,
                    'is_embedded': True
                }
            ]
        }


class TestObjectByMaterialTypeCount:

    def test_one_opaque_object_success(self, create_opaque_materialtype_object):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'opaque_type_objects': {
                    'count': 1,
                    'comparator': '=',
                },
                'blend_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'objectByMaterialTypeCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [{'id': 0, 'type': ['OPAQUE']}]
        }

    def test_one_blend_object_success(self, create_blend_materialtype_object):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'opaque_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
                'blend_type_objects': {
                    'count': 1,
                    'comparator': '=',
                },
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'objectByMaterialTypeCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [{'id': 0, 'type': ['BLEND']}]
        }

    def test_one_blend_object_failed(self, create_blend_materialtype_object):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'opaque_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
                'blend_type_objects': {
                    'count': 3,
                    'comparator': '>=',
                },
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'count of objects for each material type (opaque, blend, clip)',
            'identifier': 'objectByMaterialTypeCount',
            'msg_type': 'error',
            'items': [{
                'message': '{found} {object_type} objects found in scene that is not '
                '"{comparator}" the acceptable: {expected}',
                'object_type': 'BLEND',
                'comparator': '>=',
                'found': 1,
                'expected': 3
            }]
        }]

        for check in runner.checks:
            if check.key == 'objectByMaterialTypeCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [{'id': 0, 'type': ['BLEND']}]
        }

    def test_opaque_and_blend_object_success(self, create_opaque_blend_materialtype_scene):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'opaque_type_objects': {
                    'count': 2,
                    'comparator': '<',
                },
                'blend_type_objects': {
                    'count': 0,
                    'comparator': '>',
                },
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

        for check in runner.checks:
            if check.key == 'objectByMaterialTypeCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {'id': 0, 'type': ['BLEND']},
                {'id': 1, 'type': ['OPAQUE']}
            ]
        }

    def test_multimat_object_failed(self, create_multimaterial_materialtype_scene):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'opaque_type_objects': {
                    'count': 0,
                    'comparator': '>',
                },
                'blend_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
                'clip_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'count of objects for each material type (opaque, blend, clip)',
            'identifier': 'objectByMaterialTypeCount',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{found} {object_type} objects found in scene that is not '
                    '"{comparator}" the acceptable: {expected}',
                    'object_type': 'OPAQUE',
                    'comparator': '>',
                    'found': 0,
                    'expected': 0
                },
                {
                    'message': '{found} {object_type} objects found in scene that is not '
                    '"{comparator}" the acceptable: {expected}',
                    'object_type': 'BLEND',
                    'comparator': '=',
                    'found': 1,
                    'expected': 0
                },
                {
                    'message': '{found} {object_type} objects found in scene that is not '
                    '"{comparator}" the acceptable: {expected}',
                    'object_type': 'CLIP',
                    'comparator': '=',
                    'found': 1,
                    'expected': 0
                }
            ]}]

        for check in runner.checks:
            if check.key == 'objectByMaterialTypeCount':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {'id': 0, 'type': ['OPAQUE', 'BLEND']},
                {'id': 1, 'type': ['OPAQUE', 'CLIP']}
            ]
        }

    def test_one_opaque_object_one_shadow_plane_without_custom_property_fail(
        self,
        create_empty_scene,
        create_opaque_materialtype_object,
        create_shadow_plane
    ):
        shadow_plane = create_shadow_plane
        del shadow_plane['is_shadow_plane']

        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'blend_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
                'clip_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
            },
        }

        runner = cgtcheck.runners.CheckRunner(checks_spec=checks_spec)
        runner.runall()

        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'count of objects for each material type (opaque, blend, clip)',
            'identifier': 'objectByMaterialTypeCount',
            'msg_type': 'error',
            'items': [{
                'message': '{found} {object_type} objects found in scene '
                           'that is not "{comparator}" the acceptable: {expected}',
                'object_type': 'BLEND',
                'comparator': '=',
                'expected': 0,
                'found': 1
            }]
        }]

        properties = next(
            check for check in runner.checks
            if check.key == 'objectByMaterialTypeCount'
        ).format_properties()
        assert properties == {
            'objects': [
                {'id': 0, 'type': ['OPAQUE']},
                {'id': 1, 'type': ['BLEND']}
            ]
        }

    def test_one_opaque_object_one_shadow_plane_with_custom_property_success(
        self,
        create_empty_scene,
        create_opaque_materialtype_object,
        create_shadow_plane
    ):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['objectByMaterialTypeCount'] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'blend_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
                'clip_type_objects': {
                    'count': 0,
                    'comparator': '=',
                },
            },
        }

        runner = cgtcheck.runners.CheckRunner(checks_spec=checks_spec)
        runner.runall()

        assert runner.passed is True
        assert runner.format_reports() == []

        properties = next(
            check for check in runner.checks
            if check.key == 'objectByMaterialTypeCount'
        ).format_properties()
        assert properties == {
            'objects': [
                {'id': 0, 'type': ['OPAQUE']},
                {'id': 1, 'type': ['BLEND']}
            ]
        }


class TestNoTransparentMeshes:
    _check_key = 'noTransparentMeshes'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_transparent_meshes_success(
        self,
        create_texture_obj,
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
                    'materials': [0],
                    'transparent': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_transparent_meshes_failed(
        self,
        create_transparent_material_obj,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects containing transparent materials',
            'identifier': self._check_key,
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Object "{item}" has transparent material(s): {materials}',
                    'item': 'alpha_cube',
                    'materials': '"Material_opaque"'
                },
                {
                    'message': 'Object "{item}" has transparent material(s): {materials}',
                    'item': 'blend_cube',
                    'materials': '"Material_blend_method"'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'materials': [1],
                    'transparent': True
                },
                {
                    'id': 1,
                    'materials': [0],
                    'transparent': True
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_transparent_meshes_no_material(
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
                    'materials': [],
                    'transparent': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_opaque_mesh_and_a_shadow_plane_with_custom_property_success(
        self,
        create_empty_scene,
        create_basic_cube,
        create_shadow_plane,
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
                    'materials': [],
                    'transparent': False
                },
                {
                    'id': 1,
                    'materials': [0],
                    'transparent': True
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_opaque_mesh_and_a_shadow_plane_no_custom_property_fail(
        self,
        create_empty_scene,
        create_basic_cube,
        create_shadow_plane,
        runner: cgtcheck.runners.CheckRunner
    ):
        shadow_plane = create_shadow_plane
        del shadow_plane['is_shadow_plane']

        runner.runall()

        assert runner.passed is False
        assert runner.format_reports() == [
            {
                'message': 'Objects containing transparent materials',
                'identifier': 'noTransparentMeshes',
                'msg_type': 'error',
                'items': [
                    {
                        'message': 'Object "{item}" has transparent material(s): {materials}',
                        'item': 'shadow_plane',
                        'materials': '"Material"'}
                ]
            }
        ]

        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'materials': [],
                    'transparent': False
                },
                {
                    'id': 1,
                    'materials': [0],
                    'transparent': True
                }
            ]
        }


class TestResetTransforms:
    _check_key = 'dccResetTransforms'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
        'parameters': {
            'position': True,
            'rotation': True,
            'scale': True,
            'floatTolerance': 0.001,
            'allowInstances': False,
            'xAxisRotation': 0,
            'yAxisRotation': 0,
            'zAxisRotation': 0
        }
    }

    def test_reset_transforms_meshes_success(
        self,
        create_empty_scene,
        create_basic_cube
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
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
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, 0.0, 0.0],
                    'scale': [1.0, 1.0, 1.0]
                }
            ]
        }

    def test_reset_transforms_meshes_failed(
        self,
        non_reseted_transform_scene
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [
            {
                'message': 'Objects have non-reset transforms',
                'identifier': self._check_key,
                'msg_type': 'error',
                'items': [
                    {
                        'message': '{item} is {transformedKindsText}',
                        'item': 'r_suzanne',
                        'expected': False,
                        'found': True,
                        'translated': False,
                        'rotated': True,
                        'scaled': False,
                        'transformedKindsText': 'rotated'
                    },
                    {
                        'message': '{item} is {transformedKindsText}',
                        'item': 's_suzanne',
                        'expected': False,
                        'found': True,
                        'translated': False,
                        'rotated': False,
                        'scaled': True,
                        'transformedKindsText': 'scaled'
                    },
                    {
                        'message': '{item} is {transformedKindsText}',
                        'item': 't_suzanne',
                        'expected': False,
                        'found': True,
                        'translated': True,
                        'rotated': False,
                        'scaled': False,
                        'transformedKindsText':
                        'translated'
                    }
                ]
            }
        ]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, -0.0, 45.0],
                    'scale': [1.0, 1.0, 1.0]
                },
                {
                    'id': 1,
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, -0.0, 0.0],
                    'scale': [0.9, 1.0, 1.0]
                },
                {
                    'id': 2,
                    'position': [0.002, 0.4, -2.0],
                    'rotation': [0.0, -0.0, 0.0],
                    'scale': [1.0, 1.0, 1.0]
                }
            ]
        }

    def test_reset_transforms_allow_linked_duplicates_success(
        self,
        non_reseted_transforms_linked_duplicates
    ):
        checks_spec = deepcopy(self.checks_spec)
        checks_spec[self._check_key]['parameters'].update({'allowInstances': True})
        runner = cgtcheck.runners.CheckRunner(checks_spec=checks_spec)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_reset_transforms_allow_linked_duplicates_failed(
        self,
        non_reseted_transforms_linked_duplicates
    ):
        checks_spec = deepcopy(self.checks_spec)
        checks_spec[self._check_key]['parameters'].update({'allowInstances': False})
        runner = cgtcheck.runners.CheckRunner(checks_spec=checks_spec)
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [
            {
                'message': 'Objects have non-reset transforms',
                'identifier': self._check_key,
                'msg_type': 'error',
                'items': [
                    {
                        'message': '{item} is {transformedKindsText}',
                        'item': 'Suzanne.001',
                        'expected': False,
                        'found': True,
                        'translated': True,
                        'rotated': False,
                        'scaled': False,
                        'transformedKindsText': 'translated'
                    }
                ]
            }
        ]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [0.0, 0.0, 0.0],
                    'scale': [1.0, 1.0, 1.0]
                },
                {
                    'id': 1,
                    'position': [2.0, 0.0, 0.0],
                    'rotation': [0.0, -0.0, 0.0],
                    'scale': [1.0, 1.0, 1.0]
                }
            ]
        }

    def test_reset_transforms_rotated_model_success(
        self,
        rotated_model
    ):
        checks_spec = deepcopy(self.checks_spec)
        checks_spec[self._check_key]['parameters'].update({'xAxisRotation': 90})
        runner = cgtcheck.runners.CheckRunner(checks_spec=checks_spec)
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
                    'position': [0.0, 0.0, 0.0],
                    'rotation': [90.0, -0.0, 0.0],
                    'scale': [1.0, 1.0, 1.0]
                }
            ]
        }


class TestTexelDensity:
    _check_key = 'texelDensity'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'parameters': {
            'expected_density': 1024,
            'density_deviation': 0.1,
            'ignore_materials': ['.*_foo$', '.*BB$']
        },
        'enabled': True,
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_texel_density_success(
        self,
        create_objects_with_materials_and_textures,
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
                    'id': 1,
                    'material': 0,
                    'density': 10.24
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_texel_density_failed(
        self,
        create_embedded_texture_obj,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Incorrect texel density',
            'identifier': self._check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{material}" on object "{item}", '
                               'expected: {expected}, found: {found}',
                    'item': 'embedded_texture_cube',
                    'expected': 10.24,
                    'found': 0.00625,
                    'material': 'Material'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'material': 0,
                    'density': 0.00625
                }
            ]
        }


class TestInconsistentTexelDensity:
    _check_key = 'inconsistentTexelDensity'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'parameters': {
            'density_deviation': 0.1
        },
        'enabled': True
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    @pytest.mark.parametrize('create_texel_density_obj', [[1, 1.1]], indirect=True)
    def test_inconsistent_texel_density_success(
        self,
        create_texel_density_obj,
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
                    'id': 1,
                    'material': 0,
                    'density': 0.01
                },
                {
                    'id': 0,
                    'material': 1,
                    'density': 0.01
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_inconsistent_texel_density_no_textures_success(
        self,
        create_texel_density_obj_no_texture,
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
                    'material': 0,
                    'density': 5.12
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    @pytest.mark.parametrize('create_texel_density_obj', [[1, 12.5]], indirect=True)
    def test_inconsistent_texel_density_failed(
        self,
        create_texel_density_obj,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Inconsistent texel density',
            'identifier': self._check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Expected a texel density deviation of no more than: '
                               '{expected}, found: {found} (ranges from {min_density} '
                               'to {max_density})',
                    'expected': 0.1,
                    'found': 0.115,
                    'min_density': 0.125,
                    'max_density': 0.01
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 1,
                    'material': 0,
                    'density': 0.01
                },
                {
                    'id': 0,
                    'material': 1,
                    'density': 0.125
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_inconsistent_texel_density_ignores_no_materials(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        properties = next(
            check for check in runner.checks if check.key == self._check_key
        ).format_properties()
        assert properties == {
            'objects': []
        }


class TestFlippedUv:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['flippedUv'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_flipped_uv_success(
        self,
        create_empty_scene,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'flippedUv':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_without_flipped_faces': ['UVMap'],
                    'uv_with_flipped_faces': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_flipped_uv_tiling_failed(
        self,
        create_flipped_uv,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Flipped UV found in objects',
            'identifier': 'flippedUv',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" has flipped UVs in UV layer(s): {uv_layers}',
                    'item': 'plane_flipped_uv',
                    'uv_layers': '"flipped_uv", "flipped_uv_2"'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'flippedUv':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_without_flipped_faces': ['UVMap', 'correct_uv'],
                    'uv_with_flipped_faces': ['flipped_uv', 'flipped_uv_2']
                }
            ]
        }


class TestOverlappedUvPerObject:

    key = 'overlappedUvPerObject'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[key] = {
        'enabled': True,
        'type': 'warning'
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_success(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        create_basic_cube
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'no_overlapped_uv': ['UVMap'],
                    'overlapped_uv': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_hidden_are_ignored(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_hidden_objects,
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {'id': 0, 'no_overlapped_uv': ['UVMap'], 'overlapped_uv': []},
                {'id': 1, 'no_overlapped_uv': ['UVMap'], 'overlapped_uv': []},
                {'id': 2, 'no_overlapped_uv': ['UVMap'], 'overlapped_uv': []},
                {'id': 3, 'no_overlapped_uv': ['UVMap'], 'overlapped_uv': []},
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_object_failed(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_overlapped_uv
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': cgtcheck.metadata.checks[self.key].msg,
            'identifier': self.key,
            'msg_type': cgtcheck.metadata.checks[self.key].params['type'],
            'items': [
                {
                    'message': cgtcheck.metadata.checks[self.key].item_msg,
                    'item': '"box_overlapped_uv"',
                    'msg_type': 'in UV layer(s)):',
                    'uv_layers': '"overlapped_uv", "overlapped_uv_2"'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['UVMap']
                },
                {
                    'id': 1,
                    'overlapped_uv': ['overlapped_uv', 'overlapped_uv_2'],
                    'no_overlapped_uv': ['UVMap']
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_object_collapsed_uv_failed(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_collapsed_uv
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': cgtcheck.metadata.checks[self.key].msg,
            'identifier': self.key,
            'msg_type': cgtcheck.metadata.checks[self.key].params['type'],
            'items': [
                {
                    'message': cgtcheck.metadata.checks[self.key].item_msg,
                    'item': '"box_collapsed_uv"',
                    'msg_type': 'in UV layer(s)):',
                    'uv_layers': '"collapsed_uv"'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['UVMap']
                },
                {
                    'id': 1,
                    'overlapped_uv': ['collapsed_uv'],
                    'no_overlapped_uv': []
                }
            ]
        }


class TestOverlappedUvPerModel:

    key = 'overlappedUvPerModel'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[key] = {
        'enabled': True,
        'type': 'warning'
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_success(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        create_basic_cube
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'no_overlapped_uv': ['basic_cube'],
                    'overlapped_uv': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_model_failed(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_three_cubes_with_overlapped_uv
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': cgtcheck.metadata.checks[self.key].msg,
            'identifier': self.key,
            'msg_type': cgtcheck.metadata.checks[self.key].params['type'],
            'items': [
                {
                    'message': cgtcheck.metadata.checks[self.key].item_msg,
                    'item': '"box", "box_overlapped_uv"',
                    'msg_type': 'among themselves',
                    'uv_layers': ''
                }
            ]
        }]

        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': ['box'],
                    'no_overlapped_uv': []
                },
                {
                    'id': 1,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['box_moved_uv']
                },
                {
                    'id': 2,
                    'overlapped_uv': ['box_overlapped_uv'],
                    'no_overlapped_uv': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_ignores_missing_uvs(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        create_basic_cube
    ):
        create_basic_cube.data.uv_layers.remove(create_basic_cube.data.uv_layers[0])
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': []
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_ignores_missing_uvs_multiple_objs(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_three_cubes_with_overlapped_uv
    ):
        _box_overlapped_uv, _box, box_moved_uv = create_three_cubes_with_overlapped_uv
        box_moved_uv.data.uv_layers.remove(box_moved_uv.data.uv_layers[0])
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': cgtcheck.metadata.checks[self.key].msg,
            'identifier': self.key,
            'msg_type': cgtcheck.metadata.checks[self.key].params['type'],
            'items': [
                {
                    'message': cgtcheck.metadata.checks[self.key].item_msg,
                    'item': '"box", "box_overlapped_uv"',
                    'msg_type': 'among themselves',
                    'uv_layers': ''
                }
            ]
        }]

        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': ['box'],
                    'no_overlapped_uv': []
                },
                {
                    'id': 2,
                    'overlapped_uv': ['box_overlapped_uv'],
                    'no_overlapped_uv': []
                }
            ]
        }


class TestOverlappedUvPerMaterial:

    key = 'overlappedUvPerMaterial'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[key] = {
        'enabled': True,
        'type': 'warning'
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_success(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_two_cubes_with_overlapped_uv_but_different_materials
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'materials': [
                {
                    'material': 0,
                    'overlaps': []
                },
                {
                    'material': 1,
                    'overlaps': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_material_failed(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_two_cubes_with_overlapped_uv_by_material
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': cgtcheck.metadata.checks[self.key].msg,
            'identifier': self.key,
            'msg_type': cgtcheck.metadata.checks[self.key].params['type'],
            'items': [
                {
                    'message': cgtcheck.metadata.checks[self.key].item_msg,
                    'item': '"box_a", "box_b"',
                    'msg_type': 'in UV layer(s)):',
                    'uv_layers': '"UVMap", "a_uv"'
                }
            ]
        }]

        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'materials': [
                {
                    'material': 0,
                    'overlaps': [
                        {'object': 0, 'uv_layers': ['a_uv']},
                        {'object': 1, 'uv_layers': ['UVMap']},
                    ]
                }
            ]
        }


class TestOpenEdges:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['openEdges'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_open_edges_success(
        self,
        create_two_cubes_not_at_origin,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'openEdges':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'open_edges': False
                },
                {
                    'id': 1,
                    'open_edges': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_no_open_edges_failed(
        self,
        box_with_open_edges,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Object contains open edges',
            'identifier': 'openEdges',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" contains open edges',
                    'item': 'cube_open_edges'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'openEdges':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'open_edges': True
                }
            ]
        }


class TestNonManifoldVertices:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['nonManifoldVertices'] = {
        'enabled': True,
        'type': 'warning',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_non_manifold_vertices_success(
        self,
        create_two_cubes_not_at_origin,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'nonManifoldVertices':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'non_manifold_vertices': False
                },
                {
                    'id': 1,
                    'non_manifold_vertices': False
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_non_manifold_vertices_failed(
        self,
        mesh_with_isolated_vertex,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Object contains non-manifold vertices',
            'identifier': 'nonManifoldVertices',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Object "{item}" contains non-manifold vertices',
                    'item': 'mesh_with_isolated_vertex'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'nonManifoldVertices':
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'non_manifold_vertices': True
                }
            ]
        }

        reset_blender_scene()


class TestConnectedTextures:
    check_key = 'connectedTextures'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[check_key] = {
        'enabled': True,
        'type': 'warning',
    }

    checks_spec_permissive = deepcopy(checks_spec)
    checks_spec_permissive[check_key] = deepcopy(checks_spec[check_key])
    checks_spec_permissive[check_key].update({
        'parameters': {
            'required': [],
            'forbidden': [],
        }
    })

    checks_spec_forbidden = deepcopy(checks_spec)
    checks_spec_forbidden[check_key] = deepcopy(checks_spec[check_key])
    checks_spec_forbidden[check_key].update({
        'parameters': {
            'required': [],
            'forbidden': ['base_color'],
        }
    })

    def test_connected_tex_passes_with_no_requirements(
        self,
        create_opaque_materialtype_object_nodes,
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec_permissive)
        runner.runall()
        assert runner.format_reports() == []
        assert runner.passed is True
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'slots': []
                }
            ]
        }

    def test_connected_tex_passes_with_no_nodes_mat_no_requirements(
        self,
        create_opaque_materialtype_object,
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {'materials': []}

    def test_connected_tex_passes_no_materials(
        self,
        create_basic_cube,
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {'materials': []}

    def test_connected_tex_fails_with_missing_required_tex(
        self,
        create_opaque_materialtype_object_nodes
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Material does not meet connected textures requirements',
            'identifier': self.check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{item}" is missing textures for slots: {missing}',
                    'item': 'opaque_mat',
                    'missing': ['base_color', 'metallic', 'roughness'],
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'slots': []
                }
            ]
        }

    def test_connected_tex_passes_with_met_requirements(
        self,
        create_texture_obj_shared_color_rough_metallic,
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'slots': ['base_color', 'metallic', 'roughness'],
                }
            ]
        }

    def test_connected_tex_fails_with_forbidden_tex(
        self,
        create_texture_obj,
    ):
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec_forbidden)
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Material does not meet connected textures requirements',
            'identifier': self.check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{item}" is using textures at forbidden slots: {forbidden}',  # noqa E501
                    'item': 'Material',
                    'forbidden': ['base_color'],
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'slots': ['base_color']
                }
            ]
        }


class TestPotentialTextures:
    check_key = 'potentialTextures'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[check_key] = {
        'enabled': True,
        'type': 'warning',
    }

    checks_spec_permissive = deepcopy(checks_spec)
    checks_spec_permissive[check_key] = deepcopy(checks_spec[check_key])
    checks_spec_permissive[check_key].update({
        'parameters': {
            'required': [],
        }
    })

    checks_spec_extra_req = deepcopy(checks_spec)
    checks_spec_extra_req[check_key] = deepcopy(checks_spec[check_key])
    checks_spec_extra_req[check_key].update({
        'parameters': {
            'required': ['specular', 'ior'],
        }
    })

    # Fixtures

    @pytest.fixture
    def scene_with_no_files(self, tmpdir: str) -> Tuple[str, List[str]]:
        """
        Saves current scene file and places textures which are named properly.
        The file structure is flat.
        """
        reset_blender_scene()
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = 'cube'

        mat = bpy.data.materials.new('cube_mat')
        cube.data.materials.append(mat)
        mat.use_nodes = True

        mainfile = os.path.join(tmpdir, 'mainfile.fbx')
        bpy.ops.export_scene.fbx(filepath=mainfile)

        return mainfile, []

    @pytest.fixture
    def scene_with_decently_named_flat_files(self, tmpdir: str) -> Tuple[str, List[str]]:
        """
        Saves current scene file and places textures which are named properly.
        The file structure is flat.
        """
        reset_blender_scene()
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        cube.name = 'cube'

        mat = bpy.data.materials.new('cube_mat')
        cube.data.materials.append(mat)
        mat.use_nodes = True

        mainfile = os.path.join(tmpdir, 'mainfile.fbx')
        bpy.ops.export_scene.fbx(filepath=mainfile)

        files = [
            'mainfile_cube_mat color.jpg',
            'mainfile--cube_mat roughness.png',
            'cube_mat_Normal.png',
            'cube_matAO.psd',
            'whatever CUBE_mat_metallic.png',
            'unrelated_file.tiff',
            'something_emission.jpg',
        ]
        filepaths = [os.path.join(tmpdir, fn) for fn in files]
        for fpath in filepaths:
            open(os.path.join(tmpdir, fpath), 'wb').close()

        return mainfile, filepaths

    # Tests

    def test_potential_tex_passes_with_no_requirements(
        self,
        scene_with_no_files: Tuple[str, List[str]],
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec_permissive,
            checks_data={'input_file': scene_with_no_files[0]}
        )
        runner.runall()
        assert runner.format_reports() == []
        assert runner.passed is True
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'matches': {}
                }
            ]
        }

    def test_potential_tex_passes_with_met_requirements(
        self,
        scene_with_decently_named_flat_files,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data={'input_file': scene_with_decently_named_flat_files[0]}
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'matches': {
                        'color': list('ADEF'),
                        'roughness': list('ADEF'),
                        'metallic': list('DEF'),
                        'normal': list('ADEF'),
                        'emissive': list('DEF'),
                        'occlusion': list('ABD'),
                    }
                }
            ]
        }

    def test_potential_tex_fails_with_missing_default_required_tex(
        self,
        scene_with_no_files,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data={'input_file': scene_with_no_files[0]}
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Required texture files were not found',
            'identifier': self.check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'No potential "{type}" texture file found for material "{item}"',
                    'item': 'cube_mat',
                    'type': 'color',
                }, {
                    'message': 'No potential "{type}" texture file found for material "{item}"',
                    'item': 'cube_mat',
                    'type': 'metallic',
                }, {
                    'message': 'No potential "{type}" texture file found for material "{item}"',
                    'item': 'cube_mat',
                    'type': 'roughness',
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'matches': {}
                }
            ]
        }

    def test_potential_tex_fails_with_missing_extra_required_tex(
        self,
        scene_with_decently_named_flat_files,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec_extra_req,
            checks_data={'input_file': scene_with_decently_named_flat_files[0]}
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Required texture files were not found',
            'identifier': self.check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'No potential "{type}" texture file found for material "{item}"',
                    'item': 'cube_mat',
                    'type': 'ior',
                }, {
                    'message': 'No potential "{type}" texture file found for material "{item}"',
                    'item': 'cube_mat',
                    'type': 'specular',
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'id': 0,
                    'matches': {
                        'color': list('ADEF'),
                        'roughness': list('ADEF'),
                        'metallic': list('DEF'),
                        'normal': list('ADEF'),
                        'emissive': list('DEF'),
                        'occlusion': list('ABD'),
                    }
                }
            ]
        }


class TestDisplayedUnitScale:
    check_key = 'displayedUnits'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_displayed_units_success(self, create_basic_cube_cm):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {'desiredUnit': 'cm'},
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {'displayedUnitScale': 'centimeters'}
                break

    def test_displayed_units_failed(self, create_basic_cube_cm):

        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {'desiredUnit': 'm'},
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Unit in scene settings used to display length values '
                       'is different from required unit',
            'identifier': self.check_key,
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Expected: {expected}, found: {found}',
                    'expected': 'meters',
                    'found': 'centimeters'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {'displayedUnitScale': 'centimeters'}
                break

    def test_displayed_units_not_in_dcc(self, create_basic_cube_cm):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {'desiredUnit': 'dm'},
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {'displayedUnitScale': 'centimeters'}
                break


class TestDccdUnitScale:
    check_key = 'dccUnitScale'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_dcc_units_scale_success(self, create_basic_cube_cm):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {'desiredUnit': 'cm'},
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {'dccUnitScale': 0.01}
                break

    def test_dcc_units_scale_failed(self, create_basic_cube_cm):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {'desiredUnit': 'foot'},
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Unit scale in scene settings used to conversions '
                       'is different from required unit',
            'identifier': self.check_key,
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Expected: {expected}, found: {found}',
                    'expected': '0.304799998',
                    'found': '0.01'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {'dccUnitScale': 0.01}
                break


class TestCheckMaterialNames:
    check_key = 'unparseableMaterialName'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[check_key] = {
        'enabled': True,
    }

    material_regex = '^M_\\d+_(\\d+)$'
    material_not_matching_regex = 'Material'
    material_matching_regex = 'M_2_3'
    tex_spec = {
        'input_files': {
            'opacity': '^M_0_{matid}_{infilename}_Opacity.png',
        },
        'output_files': {},
        'parsed_variables': {
            "matid": material_regex
        },
        'required_textures': [],
        'input_directories': [],
        'predefined_variables': {},
    }

    def test_empty_tex_paths_success(self):
        reset_blender_scene()
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_material_name_correct(
        self,
        required_textures_dummy_file,
    ):
        checks_data = {
            'tex_paths': {self.material_matching_regex: {}},
            'input_file': required_textures_dummy_file,
            'tex_spec': self.tex_spec
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize(
        'objects_with_materials',
        [[[material_matching_regex, material_not_matching_regex]]],
        indirect=True
    )
    def test_material_name_incorrect(
        self,
        required_textures_dummy_file,
        objects_with_materials: pytest.fixture,
    ):
        checks_data = {
            'tex_paths': {
                self.material_not_matching_regex: {},
                self.material_matching_regex: {},
            },
            'input_file': required_textures_dummy_file,
            'tex_spec': self.tex_spec
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Incorrect material name',
            'identifier': 'unparseableMaterialName',
            'msg_type': 'error',
            'items': [{
                'message': 'Expected: {expected}, found: {found}',
                'expected': 'M_(digit)_(digit)',
                'found': 'Material'
            }]
        }]
        this_check = next(check for check in runner.checks if check.key == self.check_key)
        assert this_check.format_properties() == {
            'materials': [
                {
                    'material': 1,
                    'expected': 'M_(digit)_(digit)'
                }
            ]
        }


class TestDccObjectTypes:
    check_key = 'dccObjectTypes'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_dcc_object_types_success(self, object_with_triangles):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'forbidMesh': False,
                'forbidNull': False,
                'forbidCamera': False,
                'forbidLight': False,
                'target': 'fbx'
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'MESH': ['cylinder', 'cylinder_tris']
                }
                break

    def test_dcc_object_no_target(self, object_with_triangles):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'forbidMesh': False,
                'forbidNull': False,
                'forbidCamera': False,
                'forbidLight': False
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'MESH': ['cylinder', 'cylinder_tris'],
                }
                break

    def test_dcc_object_types_failed(self, light_meshes_empties_cameras):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'forbidMesh': True,
                'forbidNull': True,
                'forbidCamera': True,
                'forbidLight': True,
                'target': 'fbx',
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Scene contains forbidden object types',
            'identifier': self.check_key,
            'msg_type': 'error',
            'items': [{
                'message': '{item} ({type})',
                'item': 'armature00',
                'type': 'Armature'
            }, {
                'message': '{item} ({type})',
                'item': 'armature01',
                'type': 'Armature'
            }, {
                'message': '{item} ({type})',
                'item': 'cam00',
                'type': 'Camera'
            }, {
                'message': '{item} ({type})',
                'item': 'cam01',
                'type': 'Camera'
            }, {
                'message': '{item} ({type})',
                'item': 'cube00',
                'type': 'Mesh'
            }, {
                'message': '{item} ({type})',
                'item': 'cube01',
                'type': 'Mesh'
            }, {
                'message': '{item} ({type})',
                'item': 'curve00',
                'type': 'Curve'
            }, {
                'message': '{item} ({type})',
                'item': 'curve01',
                'type': 'Curve'
            }, {
                'message': '{item} ({type})',
                'item': 'empty00',
                'type': 'Empty'
            }, {
                'message': '{item} ({type})',
                'item': 'empty01',
                'type': 'Empty'
            }, {
                'message': '{item} ({type})',
                'item': 'light00',
                'type': 'Light'
            }, {
                'message': '{item} ({type})',
                'item': 'light01',
                'type': 'Light'
            }, {
                'message': '{item} ({type})',
                'item': 'metaball00',
                'type': 'Meta'
            }, {
                'message': '{item} ({type})',
                'item': 'metaball01',
                'type': 'Meta'
            }, {
                'message': '{item} ({type})',
                'item': 'surface00',
                'type': 'Surface'
            }, {
                'message': '{item} ({type})',
                'item': 'surface01',
                'type': 'Surface'
            }, {
                'message': '{item} ({type})',
                'item': 'text00',
                'type': 'Font'
            }, {
                'message': '{item} ({type})',
                'item': 'text01',
                'type': 'Font'
            }]
        }]

        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'ARMATURE': ['armature00', 'armature01'],
                    'CAMERA': ['cam00', 'cam01'],
                    'CURVE': ['curve00', 'curve01'],
                    'EMPTY': ['empty00', 'empty01'],
                    'FONT': ['text00', 'text01'],
                    'LIGHT': ['light00', 'light01'],
                    'MESH': ['cube00', 'cube01'],
                    'META': ['metaball00', 'metaball01'],
                    'SURFACE': ['surface00', 'surface01']
                }
                break


class TestDccObjectNames:
    check_key = 'dccObjectNames'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_dcc_object_names_success(self, object_with_triangles):
        checks_data = {'uid': 'uid'}
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'parsedVars': {
                    'uid': '(.+)',
                },
                'mesh': '.+',
                'empty': '.+'
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'empties': [],
                    'objects': ['cylinder', 'cylinder_tris']
                }
                break

    def test_dcc_object_names_failed(self, object_with_triangles):
        checks_data = {'uid': 'SM_Tabletop12_LOD0'}
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'parsedVars': {
                    'uid': r'SM_(\w+)_LOD\d+'
                },
                'mesh': r'^SM_{uid}(?:\d{2}){0,}$'
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Objects found which do not meet naming requirements',
            'identifier': self.check_key,
            'msg_type': 'error',
            'items': [{
                'message': '{type}: Expected: {expected}, found: {found}',
                'found': 'cylinder',
                'expected': 'SM_SM_Tabletop12_LOD0?:(digit){2}{0,}',
                'type': 'Mesh'
            }, {
                'message': '{type}: Expected: {expected}, found: {found}',
                'found': 'cylinder_tris',
                'expected': 'SM_SM_Tabletop12_LOD0?:(digit){2}{0,}',
                'type': 'Mesh'
            }]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'empties': [],
                    'objects': ['cylinder', 'cylinder_tris']
                }
                break


class TestDccMaterialNames:
    check_key = 'dccMaterialNames'
    checks_spec = deepcopy(checks_spec_disabled)

    def test_dcc_material_names_success(self, create_objects_with_materials_and_textures):
        checks_data = {'uid': 'uid'}
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'regex': '(.+)',
                'parsedVars': {
                    'object': '(.+)',
                    'uid': '(.+)'
                }
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'objects': [
                        {
                            'id': 0,
                            'materials': ['MI_BB']
                        },
                        {
                            'id': 1,
                            'materials': ['MI_AA']
                        }
                    ]
                }
                break

    def test_dcc_material_names_failed(self, create_objects_with_materials_and_textures):
        checks_data = {'uid': 'SM_Tabletop12_LOD0'}
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec[self.check_key] = {
            'enabled': True,
            'type': 'error',
            'parameters': {
                'regex': '^MI_{object[1]}(?:\\d{2}){0,}$',
                'parsedVars': {
                    'object': '(SM)_(\\w+)(\\d{2})',
                    'uid': '(SM)_(\\w+)_(LOD)\\d+'
                }
            },
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Materials found which do not meet naming requirements',
            'identifier': self.check_key,
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Expected: {expected}, found: {found}',
                    'found': 'MI_BB',
                    'expected': 'MI_{object[1]}?:(digit){2}{0,}'
                },
                {
                    'message': 'Expected: {expected}, found: {found}',
                    'found': 'MI_AA',
                    'expected': 'MI_{object[1]}?:(digit){2}{0,}'
                }]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                assert check.format_properties() == {
                    'objects': [
                        {
                            'id': 0,
                            'materials': ['MI_BB']
                        },
                        {
                            'id': 1,
                            'materials': ['MI_AA']
                        }
                    ]
                }
                break

        reset_blender_scene()


class TestUvUnwrappedObjects:
    _check_key = 'uvUnwrappedObjects'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_uv_unwrapped_objects_success(
        self,
        create_basic_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self._check_key:
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_amount': 1
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_uv_unwrapped_objects_failed(
        self,
        create_no_uv_cube,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'None UV channels found in objects',
            'identifier': 'uvUnwrappedObjects',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Object "{item}" has 0 UV channels',
                    'item': 'no_uv_cube'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == self._check_key:
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_amount': 0
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_uv_unwrapped_two_objects_failed(
        self,
        create_two_no_uv_cubes,
        runner: cgtcheck.runners.CheckRunner
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [
            {
                'message': 'None UV channels found in objects',
                'identifier': 'uvUnwrappedObjects',
                'msg_type': 'error',
                'items': [
                    {
                        'message': 'Object "{item}" has 0 UV channels',
                        'item': 'no_uv_cube'
                    },
                    {
                        'message': 'Object "{item}" has 0 UV channels',
                        'item': 'second_no_uv_cube'
                    }
                ]
            }
        ]
        for check in runner.checks:
            if check.key == self._check_key:
                properties = check.format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'uv_amount': 0
                },
                {
                    'id': 1,
                    'uv_amount': 0
                }
            ]
        }


class TestOverlappedUvPerUvIsland:

    key = 'overlappedUvPerUVIsland'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[key] = {
        'enabled': True,
        'type': 'warning'
    }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_island_basic_cube_success(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        create_basic_cube
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'no_overlapped_uv': ['UVMap'],
                    'overlapped_uv': []
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_island_with_island_overlapped_on_each_other_but_not_in_itself_in_success(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_empty_scene,
        create_merged_cubes_with_overlapped_uvs,
        create_basic_cube
    ):
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['UVMap']
                },
                {
                    'id': 1,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['UVMap']
                }
            ]
        }

    @pytest.mark.parametrize('runner', [checks_spec], indirect=True)
    def test_overlapped_uv_island_island_overlapped_in_itself_failed(
        self,
        runner: cgtcheck.runners.CheckRunner,
        create_overlapped_uv
    ):
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Found overlapped UV',
            'identifier': 'overlappedUvPerUVIsland',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Objects {item} has UV island with overlapped UVs '
                               '{msg_type} {uv_layers}',
                    'item': '"box_overlapped_uv"',
                    'msg_type': 'in UV layer(s)):',
                    'uv_layers': '"overlapped_uv", "overlapped_uv_2"'
                }
            ]
        }]
        properties = next(
            check for check in runner.checks if check.key == self.key
        ).format_properties()
        assert properties == {
            'objects': [
                {
                    'id': 0,
                    'overlapped_uv': [],
                    'no_overlapped_uv': ['UVMap']
                },
                {
                    'id': 1,
                    'overlapped_uv': ['overlapped_uv', 'overlapped_uv_2'],
                    'no_overlapped_uv': ['UVMap']
                }
            ]
        }
