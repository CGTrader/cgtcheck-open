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
import sys
import logging
from copy import deepcopy
from pathlib import Path

import pytest

import cgtcheck
import cgtcheck.generic.all_checks

from cgtcheck.generic.file_checks import CheckConsistentNaming

packages_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(packages_path / 'threed'))

logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

checks_keys = cgtcheck.metadata.checks.keys()
params_disabled = {'enabled': False}
checks_spec_disabled = {key: params_disabled for key in checks_keys}


class TestApi:
    """
    Tests for API compliancy of checks
    """

    def test_all_checks_have_version(self):
        missing_versions = {
            chk.__name__: chk.version for chk in cgtcheck.runners.CheckRunner._check_classes
            if chk.version in (None, (0, 0, 0))
        }
        assert not bool(missing_versions)


class TestCheckAspectRatio:

    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['textureAspectRatio'] = {
        'enabled': True,
        'type': 'warning'
    }

    def test_no_texture_spec_success(self):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data={'tex_paths': {}}
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureAspectRatio':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    def test_check_aspect_ratio_success(self, create_texture_aspect_ratio_correct):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': create_texture_aspect_ratio_correct}},
            'tex_spec': {'technical_requirements': {'aspect': 1.0}}
        }
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec, checks_data=checks_data)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_missing_texture_file_success(self):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': 'C:/nonexistent-image.jpg'}}
        }
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec, checks_data=checks_data)
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_check_aspect_ratio_failure(self, create_texture_aspect_ratio_wrong: Path):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': str(create_texture_aspect_ratio_wrong)}},
            'tex_spec': {'technical_requirements': {'aspect': 1.0}}
        }
        runner = cgtcheck.runners.CheckRunner(checks_spec=self.checks_spec, checks_data=checks_data)
        runner.runall()
        assert runner.passed is False
        reports = runner.format_reports()
        assert reports == [{
            'message': 'Wrong texture aspect ratio',
            'identifier': 'textureAspectRatio',
            'msg_type': 'warning',
            'items': [{
                'message': '"{item}" aspect ratio equals "{found}", expected "{expected}"',
                'item': create_texture_aspect_ratio_wrong.name,
                'expected': 1.0,
                'found': 2.0
            }]
        }]
        for check in runner.checks:
            if check.key == 'textureAspectRatio':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'texture_aspect_ratio_wrong.png',
                    'aspect': 2.0
                }
            ]
        }


class TestCheckMultipleFileFormats:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['multipleFileFormats'] = {
        'enabled': True,
        'type': 'warning',
    }

    def test_no_input_file_success(self):
        checks_data = {}

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'multipleFileFormats':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [['tex_1.png']],
        indirect=True)
    def test_no_file_formats_success(
        self, file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture
    ):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['multipleFileFormats'] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {}
        }
        checks_data = {
            'input_file': file_on_top_of_multiple_formats_textures_hierarchy
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            'subdir_1' + os.sep + 'tex_1.png',
            'subdir_2' + os.sep + 'tex_1.jpg',
            'tex_2.png',
            'subdir_2' + os.sep + 'subdir_3' + os.sep + 'tex_2.jpg',
        ]],
        indirect=True)
    def test_multiple_formats_with_subdirectories_success(
        self, file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture
    ):
        checks_data = {
            'input_file': file_on_top_of_multiple_formats_textures_hierarchy
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            'tex_1.png',
            'tex_1.jpg',
            'tex_1.bmp',
        ]],
        indirect=True)
    def test_3_formats_success(
        self, file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture
    ):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['multipleFileFormats'] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {
                'formats': ['jpg', 'png', 'bmp']
            }
        }
        checks_data = {
            'input_file': file_on_top_of_multiple_formats_textures_hierarchy
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            'tex_1.png',
            'tex_1.jpg',
            'tex_2.jpg',
            'tex_3.jpg',
        ]],
        indirect=True)
    def test_missing_format_failure(
        self, file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture
    ):
        checks_data = {
            'input_file': file_on_top_of_multiple_formats_textures_hierarchy
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Missing images for multiple file formats requirement',
            'identifier': 'multipleFileFormats',
            'msg_type': 'warning',
            'items': [
                {
                    'message': '{item} file is missing',
                    'item': 'tex_2.png',
                    'expected': True,
                    'found': None
                },
                {
                    'message': '{item} file is missing',
                    'item': 'tex_3.png',
                    'expected': True,
                    'found': None
                },
            ]
        }]
        for check in runner.checks:
            if check.key == 'multipleFileFormats':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'tex_1',
                    'formats': ['jpg', 'png']
                },
                {
                    'name': 'tex_2',
                    'formats': ['jpg']
                },
                {
                    'name': 'tex_3',
                    'formats': ['jpg']
                },
            ]
        }


class TestCheckIndexedColors:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['indexedColors'] = {
        'enabled': True,
        'type': 'warning',
    }

    def test_no_texture_spec_success(self):
        checks_data = {}

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'indexedColors':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    def test_indexed_colors_success(self, non_indexed_colors_image):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': non_indexed_colors_image}}
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_indexed_colors_failure(self, indexed_colors_image):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': indexed_colors_image}}
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Images with indexed colors',
            'identifier': 'indexedColors',
            'msg_type': 'warning',
            'items': [{
                'message': '{item} file uses indexed colors',
                'item': os.path.basename(indexed_colors_image),
                'expected': False,
                'found': True
            }]
        }]

    def test_multiple_textures(
        self,
        indexed_colors_image,
        non_indexed_colors_image,
    ):
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': non_indexed_colors_image
                },
                'material_name_2': {
                    'slot_type_1': non_indexed_colors_image,
                    'slot_type_2': indexed_colors_image,
                },
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Images with indexed colors',
            'identifier': 'indexedColors',
            'msg_type': 'warning',
            'items': [{
                'message': '{item} file uses indexed colors',
                'item': os.path.basename(indexed_colors_image),
                'expected': False,
                'found': True
            }]
        }]
        for check in runner.checks:
            if check.key == 'indexedColors':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'non_indexed_colors_texture.png',
                    'mode': 'RGB'
                },
                {
                    'name': 'non_indexed_colors_texture.png',
                    'mode': 'RGB'
                },
                {
                    'name': 'indexed_colors_texture.png',
                    'mode': 'P'
                }
            ]
        }


class TestCheckMinResolution:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['textureMinResolution'] = {
        'enabled': True,
        'type': 'warning',
    }

    min_width = 4
    min_height = 4
    ok_resolution = (min_width + 2, min_height + 3)
    too_low_resolution = (min_height, min_height - 2)

    tex_spec = {
        'technical_requirements': {
            'minSize': [min_width, min_height],
        }
    }

    def test_no_tex_paths_success(self):
        checks_data = {
            'tex_paths': {},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureMinResolution':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_no_tex_spec_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': {},
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_texture_res_within_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_texture_res_equals_limit_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[too_low_resolution]], indirect=True)
    def test_texture_res_outside_limit_failure(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False

        width, height = self.too_low_resolution
        assert runner.format_reports() == [{
            'message': 'Texture resolution is too low',
            'identifier': 'textureMinResolution',
            'msg_type': 'warning',
            'items': [{
                'message': 'For texture "{item}" resolution "{found}" is lower than required minimum "{expected}"',  # noqa E501
                'item': 'texture_1.png',
                'found': '{}x{}'.format(width, height),
                'expected': '{}x{}'.format(
                    self.min_width, self.min_height
                )
            }]
        }]

    @pytest.mark.parametrize(
        'textures_with_res',
        [[ok_resolution, too_low_resolution, too_low_resolution]],
        indirect=True
    )
    def test_multiple_textures_failure(self, textures_with_res: pytest.fixture):
        tex_1_ok, tex_2_fail, tex_3_fail = sorted(textures_with_res)
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1_ok
                },
                'material_name_2': {
                    'slot_type_1': tex_2_fail,
                    'slot_type_2': tex_3_fail,
                },
            },
            'tex_spec': self.tex_spec,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        width, height = self.too_low_resolution
        assert runner.format_reports() == [{
            'message': 'Texture resolution is too low',
            'identifier': 'textureMinResolution',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'For texture "{item}" resolution "{found}" is lower than required minimum "{expected}"',  # noqa E501
                    'item': 'texture_2.png',
                    'found': '{}x{}'.format(width, height),
                    'expected': '{}x{}'.format(
                        self.min_width, self.min_height
                    )
                },
                {
                    'message': 'For texture "{item}" resolution "{found}" is lower than required minimum "{expected}"',  # noqa E501
                    'item': 'texture_3.png',
                    'found': '{}x{}'.format(width, height),
                    'expected': '{}x{}'.format(
                        self.min_width, self.min_height
                    )
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'textureMinResolution':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'texture_1.png',
                    'resolution': [6, 7]
                },
                {
                    'name': 'texture_2.png',
                    'resolution': [4, 2]
                },
                {
                    'name': 'texture_3.png',
                    'resolution': [4, 2]
                }
            ]
        }

    @pytest.mark.parametrize('textures_with_res', [[too_low_resolution]], indirect=True)
    def test_plain_texture_res_outside_limit_success(self, textures_with_res: pytest.fixture):
        tex_spec = self.tex_spec.copy()
        tex_spec['technical_requirements']['minSizePlain'] = [1, 1]
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True


class TestCheckMaxResolution:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['textureMaxResolution'] = {
        'enabled': True,
        'type': 'warning',
    }

    max_width = 10
    max_height = 10
    ok_resolution = (max_width - 2, max_height - 3)
    too_high_resolution = (max_width, max_height + 2)

    tex_spec = {
        'technical_requirements': {
            'maxSize': [max_width, max_height],
        }
    }

    def test_no_tex_paths_success(self):
        checks_data = {
            'tex_paths': {},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureMaxResolution':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_no_tex_spec_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': {},
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_smaller_texture_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[ok_resolution]], indirect=True)
    def test_texture_res_equals_limit_success(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[too_high_resolution]], indirect=True)
    def test_bigger_texture_failure(self, textures_with_res: pytest.fixture):
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': self.tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False

        width, height = self.too_high_resolution
        assert runner.format_reports() == [{
            'message': 'Texture resolution is too high',
            'identifier': 'textureMaxResolution',
            'msg_type': 'warning',
            'items': [{
                'message': 'For texture "{item}" resolution "{found}" is higher than acceptable maximum "{expected}"',  # noqa E501
                'item': 'texture_1.png',
                'found': '{}x{}'.format(width, height),
                'expected': '{}x{}'.format(
                    self.max_width, self.max_height
                )
            }]
        }]

    @pytest.mark.parametrize(
        'textures_with_res',
        [[ok_resolution, too_high_resolution, too_high_resolution]],
        indirect=True,
    )
    def test_multiple_textures_failure(self, textures_with_res: pytest.fixture):
        tex_1_ok, tex_2_fail, tex_3_fail = sorted(textures_with_res)
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1_ok
                },
                'material_name_2': {
                    'slot_type_1': tex_2_fail,
                    'slot_type_2': tex_3_fail,
                },
            },
            'tex_spec': self.tex_spec,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        width, height = self.too_high_resolution
        assert runner.format_reports() == [{
            'message': 'Texture resolution is too high',
            'identifier': 'textureMaxResolution',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'For texture "{item}" resolution "{found}" is higher than acceptable maximum "{expected}"',  # noqa E501
                    'item': 'texture_2.png',
                    'found': '{}x{}'.format(width, height),
                    'expected': '{}x{}'.format(
                        self.max_width, self.max_height
                    )
                },
                {
                    'message': 'For texture "{item}" resolution "{found}" is higher than acceptable maximum "{expected}"',  # noqa E501
                    'item': 'texture_3.png',
                    'found': '{}x{}'.format(width, height),
                    'expected': '{}x{}'.format(
                        self.max_width, self.max_height
                    )
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'textureMaxResolution':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'texture_1.png',
                    'resolution': [8, 7]
                },
                {
                    'name': 'texture_2.png',
                    'resolution': [10, 12]
                },
                {
                    'name': 'texture_3.png',
                    'resolution': [10, 12]
                }
            ]
        }

    @pytest.mark.parametrize('textures_with_res', [[too_high_resolution]], indirect=True)
    def test_plain_texture_res_outside_limit_success(self, textures_with_res: pytest.fixture):
        tex_spec = self.tex_spec.copy()
        tex_spec['technical_requirements']['maxSizePlain'] = list(self.too_high_resolution)
        checks_data = {
            'tex_paths': {'material_name': {'slot_type': textures_with_res[0]}},
            'tex_spec': tex_spec,
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True


class TestCheckNoTexMaterial:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['texturelessMaterial'] = {
        'enabled': True,
        'type': 'warning',
    }
    regex = r'M(?:_\w*)*_notex'
    name_matching_regex_1 = 'M_some_name_notex'
    name_matching_regex_2 = 'M_other_name_notex'
    name_not_matching_regex_1 = 'some_material_name'
    name_not_matching_regex_2 = 'other_material_name'
    res = (4, 4)

    @pytest.mark.parametrize('textures_with_res', [[res]], indirect=True)
    def test_without_regex_success(self, textures_with_res: pytest.fixture):
        texture_1 = textures_with_res[0]
        checks_data = {
            'tex_paths': {
                self.name_matching_regex_1: {
                    'slot_type_1': texture_1
                }
            },
            'tex_spec': {}
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'texturelessMaterial':
                properties = check.format_properties()

        assert properties == {
            'textureForMaterial': [
                {
                    'regexes': {},
                    'material': self.name_matching_regex_1,
                    'texture': [os.path.basename(texture_1)]
                }
            ]
        }

    def test_without_tex_paths_success(self):
        checks_data = {
            'tex_paths': {},
            'tex_spec': {
                'parsed_variables': {
                    'notex_mat': self.regex
                }
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, res, res]], indirect=True)
    def test_without_no_tex_materials_success(self, textures_with_res: pytest.fixture):
        texture_1, texture_2, texture_3 = sorted(textures_with_res)
        checks_data = {
            'tex_paths': {
                self.name_not_matching_regex_1: {
                    'slot_type_1': texture_1
                },
                self.name_not_matching_regex_2: {
                    'slot_type_1': texture_2,
                    'slot_type_2': texture_3
                }
            },
            'tex_spec': {
                'parsed_variables': {
                    'notex_mat': self.regex
                }
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, res, res]], indirect=True)
    def test_no_tex_materials_with_textures_failure(self, textures_with_res: pytest.fixture):
        texture_1, texture_2, texture_3 = sorted(textures_with_res)
        checks_data = {
            'tex_paths': {
                self.name_not_matching_regex_2: {
                    'slot_type_1': texture_1
                },
                self.name_matching_regex_1: {
                    'slot_type_1': texture_2,
                    'slot_type_2': texture_3
                },
                self.name_matching_regex_2: {
                    'slot_type_1': texture_2
                }
            },
            'tex_spec': {
                'parsed_variables': {
                    'notex_mat': self.regex
                }
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Found textures for materials which should not use any',
            'identifier': 'texturelessMaterial',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Material "{material}" texture "{item}"',
                    'material': self.name_matching_regex_2,
                    'item': os.path.basename(texture_2)
                },
                {
                    'message': 'Material "{material}" texture "{item}"',
                    'material': self.name_matching_regex_1,
                    'item': os.path.basename(texture_2)
                },
                {
                    'message': 'Material "{material}" texture "{item}"',
                    'material': self.name_matching_regex_1,
                    'item': os.path.basename(texture_3)
                },
            ]
        }]
        for check in runner.checks:
            if check.key == 'texturelessMaterial':
                properties = check.format_properties()

        assert properties == {
            'textureForMaterial': [
                {
                    'regexes': 'M(?:_\\w*)*_notex',
                    'material': self.name_matching_regex_2,
                    'texture': [os.path.basename(texture_2)]
                },
                {
                    'regexes': 'M(?:_\\w*)*_notex',
                    'material': self.name_matching_regex_1,
                    'texture': [os.path.basename(texture_2), os.path.basename(texture_3)]
                },
                {
                    'regexes': 'M(?:_\\w*)*_notex',
                    'material': self.name_not_matching_regex_2,
                    'texture': [os.path.basename(texture_1)]
                },
            ]
        }


class TestCheckUnsupportedPNGs:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['unsupportedPng'] = {
        'enabled': True,
        'type': 'warning',
    }

    def test_no_tex_paths_success(self):
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'unsupportedPng':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[('texture1.bmp', '1'), ('texture2.tiff', 'CMYK'), ('texture3.jpg', 'RGBX')]],
        indirect=True,
    )
    def test_multiple_non_png_formats_success(self, textures_with_mode: pytest.fixture):
        tex_1_ok, tex_2_ok, tex_3_ok = textures_with_mode
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1_ok,
                    'slot_type_2': tex_2_ok,
                    'slot_type_3': tex_3_ok
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
        'textures_with_mode',
        [[
            ('texture1.png', 'RGB'),
            ('texture2.png', 'RGBA'),
            ('texture3.png', 'L'),
            ('texture4.png', 'P')
        ]],
        indirect=True,
    )
    def test_multiple_png_modes_success(self, textures_with_mode: pytest.fixture):
        tex_1_ok, tex_2_ok, tex_3_ok, tex_4_ok = textures_with_mode
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1_ok,
                    'slot_type_2': tex_2_ok,
                    'slot_type_3': tex_3_ok,
                    'slot_type_4': tex_4_ok
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_mode', [[('texture.png', 'LA')]], indirect=True)
    def test_unsupported_png_mode_failure(self, textures_with_mode: pytest.fixture):
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': textures_with_mode[0],
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Unsupported PNG images',
            'identifier': 'unsupportedPng',
            'msg_type': 'warning',
            'items': [{
                'message': '"{filename}": "{format}"',
                'filename': 'texture.png',
                'format': '8-bit pixels, black and white, with alpha'
            }]
        }]

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[('texture1.png', 'RGB'), ('texture2.png', 'LA'), ('texture3.png', 'I;16')]],
        indirect=True,
    )
    def test_multiple_unsupported_pngs_failure(self, textures_with_mode: pytest.fixture):
        tex_1_ok, tex_2_fail, tex_3_fail = textures_with_mode
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1_ok,
                    'slot_type_2': tex_2_fail
                },
                'material_name_2': {
                    'slot_type_1': tex_3_fail,
                },
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Unsupported PNG images',
            'identifier': 'unsupportedPng',
            'msg_type': 'warning',
            'items': [
                {
                    'message': '"{filename}": "{format}"',
                    'filename': 'texture2.png',
                    'format': '8-bit pixels, black and white, with alpha'
                },
                {
                    'message': '"{filename}": "{format}"',
                    'filename': 'texture3.png',
                    'format': '32-bit signed integer pixels'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'unsupportedPng':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'texture1.png',
                    'mode': 'RGB'
                },
                {
                    'name': 'texture2.png',
                    'mode': 'LA'
                },
                {
                    'name': 'texture3.png',
                    'mode': 'I'
                }
            ]
        }


class TestCheckArithmeticJpegs:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['arithmeticJpegs'] = {
        'enabled': True,
        'type': 'warning',
    }

    def test_empty_tex_paths_success(self):
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'arithmeticJpegs':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[('texture.jpg', 'RGB')]],
        indirect=True,
    )
    def test_non_arithmetic_coded_jpg_success(self, textures_with_mode: pytest.fixture):
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': textures_with_mode[0],
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    def test_arithmetic_coded_jpg_failure(self, arithmetic_coded_jpg: pytest.fixture):
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': arithmetic_coded_jpg,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Arithmetic coded JPEG images',
            'identifier': 'arithmeticJpegs',
            'msg_type': 'warning',
            'items': [{
                'message': 'Texture "{item}"',
                'item': 'arithmetic_coded.jpg'
            }]
        }]
        for check in runner.checks:
            if check.key == 'arithmeticJpegs':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'name': 'arithmetic_coded.jpg',
                    'coding': 'arithmetic'
                }
            ]
        }


class TestCheckOrmConsistentResolution:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['resolutionOrmMismatch'] = {
        'enabled': True,
        'type': 'warning',
    }
    res = (6, 6)
    other_res = (8, 8)
    yet_another_res = (10, 10)
    slot_to_check_1 = 'occlusion'
    slot_to_check_2 = 'roughness'
    slot_to_check_3 = 'metallic'

    def test_empty_tex_paths_success(self):
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'resolutionOrmMismatch':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize('textures_with_res', [[res, res, res]], indirect=True)
    def test_orm_same_resolution_success(self, textures_with_res: pytest.fixture):

        tex_1, tex_2, tex_3 = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, res, res, other_res]], indirect=True)
    def test_non_orm_textures_diffrent_resolution_success(self, textures_with_res: pytest.fixture):

        tex_1, tex_2, tex_3, tex_4_other_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3,
                    'other_slot': tex_4_other_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, res, other_res]], indirect=True)
    def test_orm_different_resolutions_failure(self, textures_with_res: pytest.fixture):

        tex_1, tex_2, tex_3_other_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    self.slot_to_check_3: tex_3_other_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': "Occlusion, Metallic and Roughness textures resolutions don't match",
            'identifier': 'resolutionOrmMismatch',
            'msg_type': 'warning',
            'items': [
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_1),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_2),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_3_other_res),
                    'resolution': '{}x{}'.format(*self.other_res)
                }
            ]
        }]

    @pytest.mark.parametrize(
        'textures_with_res', [[res, res, other_res, yet_another_res]], indirect=True
    )
    def test_orm_resolutions_mismatch_reported_for_first_materil_only(
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
            'message': "Occlusion, Metallic and Roughness textures resolutions don't match",
            'identifier': 'resolutionOrmMismatch',
            'msg_type': 'warning',
            'items': [
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_1),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_2),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_3_other_res),
                    'resolution': '{}x{}'.format(*self.other_res)
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'resolutionOrmMismatch':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'material': 'material_name_1',
                    'type': 'metallic',
                    'name': 'texture_3.png',
                    'resolution': [8, 8]
                },
                {
                    'material': 'material_name_1',
                    'type': 'occlusion',
                    'name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'material': 'material_name_1',
                    'type': 'roughness',
                    'name': 'texture_2.png',
                    'resolution': [6, 6]
                },
                {
                    'material': 'material_name_2',
                    'type': 'metallic',
                    'name': 'texture_4.png',
                    'resolution': [10, 10]
                },
                {
                    'material': 'material_name_2',
                    'type': 'occlusion',
                    'name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'material': 'material_name_2',
                    'type': 'roughness',
                    'name': 'texture_3.png',
                    'resolution': [8, 8]
                }
            ]
        }


class TestCheckColorOpacityConsistentResolution:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['resolutionsColorOpacityMismatch'] = {
        'enabled': True,
        'type': 'warning',
    }
    res = (6, 6)
    other_res = (8, 8)
    yet_another_res = (10, 10)
    slot_to_check_1 = 'color'
    slot_to_check_2 = 'opacity'

    def test_empty_tex_paths_success(self):
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'resolutionsColorOpacityMismatch':
                properties = check.format_properties()

        assert properties == {
            'texture': []
        }

    @pytest.mark.parametrize('textures_with_res', [[res, res]], indirect=True)
    def test_orm_same_resolution_success(self, textures_with_res: pytest.fixture):

        tex_1, tex_2 = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, res, other_res]], indirect=True)
    def test_non_orm_textures_diffrent_resolution_success(self, textures_with_res: pytest.fixture):

        tex_1, tex_2, tex_3_other_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2,
                    'other_slot': tex_3_other_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []

    @pytest.mark.parametrize('textures_with_res', [[res, other_res]], indirect=True)
    def test_orm_different_resolutions_failure(self, textures_with_res: pytest.fixture):

        tex_1, tex_2_other_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2_other_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': "BaseColor and Opacity textures resolutions don't match",
            'identifier': 'resolutionsColorOpacityMismatch',
            'msg_type': 'warning',
            'items': [

                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_1),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_2_other_res),
                    'resolution': '{}x{}'.format(*self.other_res)
                }
            ]
        }]

    @pytest.mark.parametrize(
        'textures_with_res', [[res, other_res, yet_another_res]], indirect=True
    )
    def test_orm_resolutions_mismatch_reported_for_first_materil_only(
        self, textures_with_res: pytest.fixture
    ):
        tex_1, tex_2_other_res, tex_3_different_res = textures_with_res
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_2_other_res,
                },
                'material_name_2': {
                    self.slot_to_check_1: tex_1,
                    self.slot_to_check_2: tex_3_different_res,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': "BaseColor and Opacity textures resolutions don't match",
            'identifier': 'resolutionsColorOpacityMismatch',
            'msg_type': 'warning',
            'items': [

                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_1),
                    'resolution': '{}x{}'.format(*self.res)
                },
                {
                    'message': '{item}, resolution "{resolution}"',
                    'item': os.path.basename(tex_2_other_res),
                    'resolution': '{}x{}'.format(*self.other_res)
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'resolutionsColorOpacityMismatch':
                properties = check.format_properties()

        assert properties == {
            'texture': [
                {
                    'material': 'material_name_1',
                    'type': 'color',
                    'name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'material': 'material_name_1',
                    'type': 'opacity',
                    'name': 'texture_2.png',
                    'resolution': [8, 8]
                },
                {
                    'material': 'material_name_2',
                    'type': 'color',
                    'name': 'texture_1.png',
                    'resolution': [6, 6]
                },
                {
                    'material': 'material_name_2',
                    'type': 'opacity',
                    'name': 'texture_3.png',
                    'resolution': [10, 10]
                }
            ]
        }


class TestCheckUnsupportedBmpCompression:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['unsupportedBmpCompression'] = {
        'enabled': True,
        'type': 'warning',
    }

    def test_empty_tex_paths_success(self):
        checks_data = {'tex_paths': {}}
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'unsupportedBmpCompression':
                properties = check.format_properties()

        assert properties == {
            'textures': []
        }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[('texture1.bmp', 'RGB'), ('texture2.bmp', 'RGB'), ('texture3.bmp', 'RGB')]],
        indirect=True,
    )
    def test_multiple_bmp_success(
        self, textures_with_mode: pytest.fixture
    ):
        tex_1, tex_2, tex_3 = textures_with_mode
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': tex_1,
                    'slot_type_2': tex_2
                },
                'material_name_2': {
                    'slot_type_1': tex_3
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
            if check.key == 'unsupportedBmpCompression':
                properties = check.format_properties()

        assert properties == {
            'textures': [
                {
                    'name': 'texture1.bmp',
                    'compression': 0
                },
                {
                    'name': 'texture2.bmp',
                    'compression': 0
                },
                {
                    'name': 'texture3.bmp',
                    'compression': 0
                }
            ]
        }

    def test_bmp_with_unsupported_compression_failure(
        self, bmp_with_unsupported_compression: pytest.fixture
    ):

        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': bmp_with_unsupported_compression,
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Textures with unsupported BMP compression',
            'identifier': 'unsupportedBmpCompression',
            'msg_type': 'warning',
            'items': [{
                'message': '"{item}"',
                'item': 'unsupported_compression.bmp'
            }]
        }]


class TestCheckUnusedTextures:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['unusedTextures'] = {
        'enabled': True,
        'type': 'warning',
    }
    texture_subpath_1 = 'subdir_1' + os.sep + 'tex_1.png'
    texture_subpath_2 = 'subdir_2' + os.sep + 'tex_2.jpg'
    texture_subpath_3 = 'tex_3.png'
    texture_subpath_4 = 'subdir_2' + os.sep + 'subdir_3' + os.sep + 'tex_4.jpg'
    texture_subpath_5_gif = 'tex_5.gif'

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[texture_subpath_1]],
        indirect=True)
    def test_no_input_file_success(
        self, file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture
    ):
        root = os.path.dirname(file_on_top_of_multiple_formats_textures_hierarchy)
        checks_data = {
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_1),
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
            if check.key == 'unusedTextures':
                properties = check.format_properties()

        assert properties == {
            'textures': []
        }

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            texture_subpath_1,
            texture_subpath_2,
            texture_subpath_3,
            texture_subpath_4
        ]],
        indirect=True)
    def test_multiple_textures_success(
        self,
        file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture,
    ):
        input_file = file_on_top_of_multiple_formats_textures_hierarchy
        root = os.path.dirname(input_file)
        checks_data = {
            'input_file': input_file,
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_1),
                    'slot_type_2': os.path.join(root, self.texture_subpath_2),
                },
                'material_name_2': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_3),
                    'slot_type_2': os.path.join(root, self.texture_subpath_4),
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
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            texture_subpath_1,
            texture_subpath_5_gif,
        ]],
        indirect=True)
    def test_not_used_texture_with_not_listed_file_format_success(
        self,
        file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture,
    ):

        input_file = file_on_top_of_multiple_formats_textures_hierarchy
        root = os.path.dirname(input_file)
        checks_data = {
            'input_file': input_file,
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_1),
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
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            texture_subpath_1,
            texture_subpath_5_gif
        ]],
        indirect=True)
    def test_custom_file_formats_not_used_texture_failure(
        self,
        file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture,
    ):
        checks_spec = deepcopy(checks_spec_disabled)
        checks_spec['unusedTextures'] = {
            'enabled': True,
            'type': 'warning',
            'parameters': {
                'formats': ['gif']
            }
        }
        input_file = file_on_top_of_multiple_formats_textures_hierarchy
        root = os.path.dirname(input_file)
        checks_data = {
            'input_file': input_file,
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_1),
                },
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Some texture files are not used',
            'identifier': 'unusedTextures',
            'msg_type': 'warning',
            'items': [{
                'message': 'Texture "{item}" could not be attached to any material',
                'item': 'tex_5.gif'
            }]
        }]

    @pytest.mark.parametrize(
        'file_on_top_of_multiple_formats_textures_hierarchy',
        [[
            texture_subpath_1,
            texture_subpath_2,
            texture_subpath_3,
            texture_subpath_4
        ]],
        indirect=True)
    def test_multiple_unused_textures_failure(
        self,
        file_on_top_of_multiple_formats_textures_hierarchy: pytest.fixture,
    ):
        input_file = file_on_top_of_multiple_formats_textures_hierarchy
        root = os.path.dirname(input_file)
        checks_data = {
            'input_file': input_file,
            'tex_paths': {
                'material_name_1': {
                    'slot_type_1': os.path.join(root, self.texture_subpath_1),
                },
                'material_name_2': {
                    'slot_type_2': os.path.join(root, self.texture_subpath_4),
                }
            }
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Some texture files are not used',
            'identifier': 'unusedTextures',
            'msg_type': 'warning',
            'items': [
                {
                    'message': 'Texture "{item}" could not be attached to any material',
                    'item': 'tex_3.png'
                },
                {
                    'message': 'Texture "{item}" could not be attached to any material',
                    'item': 'tex_2.jpg'
                }
            ]
        }]
        for check in runner.checks:
            if check.key == 'unusedTextures':
                properties = check.format_properties()

        assert properties == {
            'textures': [
                {
                    'name': 'tex_3.png',
                    'used': False
                },
                {
                    'name': 'tex_1.png',
                    'used': True
                },
                {
                    'name': 'tex_2.jpg',
                    'used': False
                },
                {
                    'name': 'tex_4.jpg',
                    'used': True
                }
            ]
        }


class TestTextureAlphaChannel:
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec['textureAlphaChannel'] = {
        'enabled': True,
        'type': 'warning',
        'parameters': {
            'color': True,
            'roughness': True,
            'metallic': True,
            'occlusion': True,
            'opacity': True,
            'normal': True,
            'emission': True
        }
    }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[
            ('M_0_0_tmp_0_BaseColor.png', 'RGB'),
            ('M_0_0_tmp_0_Roughness.png', 'RGB'),
            ('M_0_0_tmp_0_Metalness.png', 'RGB'),
            ('M_0_0_tmp_0_AO.png', 'RGB'),
            ('M_0_0_tmp_0_Opacity.png', 'RGB'),
            ('M_0_0_tmp_0_Normal.png', 'RGB'),
            ('M_0_0_tmp_0_Emissive.png', 'RGB'),
        ]],
        indirect=True)
    def test_all_enabled_no_alpha_found_passed(
        self,
        textures_with_mode: pytest.fixture
    ):
        color, roughness, metallic, occlusion, opacity, normal, emission = textures_with_mode
        checks_data = {
            'input_file': color,
            'tex_paths': {
                'M_0_0': {
                    'color': color,
                    'roughness': roughness,
                    'metallic': metallic,
                    'occlusion': occlusion,
                    'opacity': opacity,
                    'normal': normal,
                    'emission': emission
                }
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureAlphaChannel':
                properties = check.format_properties()
        assert properties == {
            'textures': [
                {'name': 'M_0_0_tmp_0_BaseColor.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Roughness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Metalness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_AO.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Opacity.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Normal.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Emissive.png', 'mode': 'RGB'},
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[
            ('M_0_0_tmp_0_BaseColor.png', 'RGB'),
            ('M_0_0_tmp_0_Roughness.png', 'RGB'),
            ('M_0_0_tmp_0_Metalness.png', 'RGB'),
            ('M_0_0_tmp_0_AO.png', 'RGBA'),
            ('M_0_0_tmp_0_Opacity.png', 'RGB'),
            ('M_0_0_tmp_0_Normal.png', 'RGBA'),
            ('M_0_0_tmp_0_Emissive.png', 'RGB'),
        ]],
        indirect=True)
    def test_all_enabled_alpha_found_failed(
        self,
        textures_with_mode: pytest.fixture
    ):
        color, roughness, metallic, occlusion, opacity, normal, emission = textures_with_mode
        checks_data = {
            'input_file': color,
            'tex_paths': {
                'M_0_0': {
                    'color': color,
                    'roughness': roughness,
                    'metallic': metallic,
                    'occlusion': occlusion,
                    'opacity': opacity,
                    'normal': normal,
                    'emission': emission
                }
            }
        }

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [
            {
                'message': 'Found textures with alpha channel',
                'identifier': 'textureAlphaChannel',
                'msg_type': 'warning',
                'items': [
                    {
                        'message': 'texture "{item}" have alpha channel',
                        'item': 'M_0_0_tmp_0_AO.png'
                    },
                    {
                        'message': 'texture "{item}" have alpha channel',
                        'item': 'M_0_0_tmp_0_Normal.png'
                    }
                ]
            }
        ]
        for check in runner.checks:
            if check.key == 'textureAlphaChannel':
                properties = check.format_properties()
        assert properties == {
            'textures': [
                {'name': 'M_0_0_tmp_0_BaseColor.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Roughness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Metalness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_AO.png', 'mode': 'RGBA'},
                {'name': 'M_0_0_tmp_0_Opacity.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Normal.png', 'mode': 'RGBA'},
                {'name': 'M_0_0_tmp_0_Emissive.png', 'mode': 'RGB'}
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_mode',
        [[
            ('M_0_0_tmp_0_BaseColor.png', 'RGB'),
            ('M_0_0_tmp_0_Roughness.png', 'RGB'),
            ('M_0_0_tmp_0_Metalness.png', 'RGB'),
            ('M_0_0_tmp_0_Normal.png', 'RGBA'),
        ]],
        indirect=True)
    def test_partially_enabled_alpha_found_passed(
        self,
        textures_with_mode: pytest.fixture
    ):
        color, roughness, metallic, normal = textures_with_mode
        checks_data = {
            'input_file': color,
            'tex_paths': {
                'M_0_0': {
                    'color': color,
                    'roughness': roughness,
                    'metallic': metallic,
                    'normal': normal
                }
            }
        }
        checks_spec = deepcopy(self.checks_spec)
        checks_spec['textureAlphaChannel']['parameters'].update({'normal': False})

        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == 'textureAlphaChannel':
                properties = check.format_properties()
        assert properties == {
            'textures': [
                {'name': 'M_0_0_tmp_0_BaseColor.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Roughness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Metalness.png', 'mode': 'RGB'},
                {'name': 'M_0_0_tmp_0_Normal.png', 'mode': 'RGBA'},
            ]
        }


class TestCheckFbxFormat:
    check_key = 'fbxFormat'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[check_key] = {
        'enabled': True,
        'type': 'warning',
        'parameters': {
            'allow_binary': True,
            'allow_ascii': False,
            'version': {'min': 7100, 'max': None},
        },
    }

    def test_binary_file_within_version_limits_passes(
        self,
        default_fbx_binary_file: pytest.fixture
    ):
        checks_data = {
            'input_file': default_fbx_binary_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data=checks_data,
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        for check in runner.checks:
            if check.key == self.check_key:
                properties = check.format_properties()
        assert properties == {'type': 'binary', 'version': 7400}

    def test_binary_file_below_version_limits_fails(
        self,
        default_fbx_binary_file: pytest.fixture
    ):
        checks_spec = deepcopy(self.checks_spec)
        checks_spec[self.check_key]['parameters'].update({
            'version': {'min': 9999, 'max': None},
        })
        checks_data = {
            'input_file': default_fbx_binary_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data,
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'FBX format not supported',
            'identifier': 'fbxFormat',
            'msg_type': 'warning',
            'items': [{
                'message': (
                    'Expected {expected_type}, version {expected_version_min} to '
                    '{expected_version_max}; found: {found_type}, version {found_version}'
                ),
                'expected_type': 'binary',
                'expected_version_min': 9999,
                'expected_version_max': None,
                'found_type': 'binary',
                'found_version': 7400,
            }]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                properties = check.format_properties()
        assert properties == {'type': 'binary', 'version': 7400}

    def test_binary_file_above_version_limits_fails(
        self,
        default_fbx_binary_file: pytest.fixture
    ):
        checks_spec = deepcopy(self.checks_spec)
        checks_spec[self.check_key]['parameters'].update({
            'version': {'min': None, 'max': 6100},
        })
        checks_data = {
            'input_file': default_fbx_binary_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=checks_spec,
            checks_data=checks_data,
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'FBX format not supported',
            'identifier': 'fbxFormat',
            'msg_type': 'warning',
            'items': [{
                'message': (
                    'Expected {expected_type}, version {expected_version_min} to '
                    '{expected_version_max}; found: {found_type}, version {found_version}'
                ),
                'expected_type': 'binary',
                'expected_version_min': None,
                'expected_version_max': 6100,
                'found_type': 'binary',
                'found_version': 7400,
            }]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                properties = check.format_properties()
        assert properties == {'type': 'binary', 'version': 7400}

    def test_ascii_file_fails_type_check(
        self,
        default_fbx_ascii_file: pytest.fixture
    ):
        checks_data = {
            'input_file': default_fbx_ascii_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec,
            checks_data=checks_data,
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'FBX format not supported',
            'identifier': 'fbxFormat',
            'msg_type': 'warning',
            'items': [{
                'message': (
                    'Expected {expected_type}, version {expected_version_min} to '
                    '{expected_version_max}; found: {found_type}, version {found_version}'
                ),
                'expected_type': 'binary',
                'expected_version_min': 7100,
                'expected_version_max': None,
                'found_type': 'ASCII',
                'found_version': 7700,
            }]
        }]
        for check in runner.checks:
            if check.key == self.check_key:
                properties = check.format_properties()
        assert properties == {'type': 'ASCII', 'version': 7700}


class TestRecommendedTexturesNaming:
    _check_key = 'recommendedTexturesNaming'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
    }
    slot_to_check_1 = 'opacity'
    slot_to_check_2 = 'roughness'
    slot_to_check_3 = 'metallic'
    first_mat = 'M_2_3'
    second_mat = 'M_5_123'
    third_mat = 'M_42'

    @pytest.mark.parametrize(
        'textures_with_mat_name_and_types', [
            {
                first_mat: ['BaseColor', 'Metalness', 'Emission'],
                second_mat: ['Metalness', 'Emission'],
                third_mat: ['BaseColor', 'Normal']
            }
        ], indirect=True
    )
    def test_textures_naming_convention_passes(
        self,
        default_fbx_ascii_file,
        textures_with_mat_name_and_types: pytest.fixture
    ):
        m1_tex_1, m1_tex_2, m1_tex_3, m2_tex_1, m2_tex_2, m3_tex1, m3_tex2\
            = textures_with_mat_name_and_types
        checks_data = {
            'tex_paths': {
                self.first_mat: {
                    self.slot_to_check_1: m1_tex_1,
                    self.slot_to_check_2: m1_tex_2,
                    self.slot_to_check_3: m1_tex_3,
                },
                self.second_mat: {
                    self.slot_to_check_1: m2_tex_1,
                    self.slot_to_check_3: m2_tex_2,
                },
                self.third_mat: {
                    self.slot_to_check_1: m3_tex1,
                    self.slot_to_check_3: m3_tex2,
                }
            },
            'input_file': default_fbx_ascii_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'texture': [
                {
                    'name': 'M_2_3_BaseColor.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_2_3_Emission.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_2_3_Metalness.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_42_BaseColor.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_42_Normal.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_5_123_Emission.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_5_123_Metalness.png',
                    'complies_with_conventions': True
                }
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_mat_name_and_types', [
            {
                first_mat: ['BASECOLOR', 'AO', 'Emission'],
                second_mat: ['Albedo', 'AmbientOcclusion'],
                third_mat: ['BaseColor', 'normal']
            }
        ], indirect=True
    )
    def test_textures_naming_convention_inconsistent_types_and_capitalization_fails(
        self,
        default_fbx_ascii_file,
        textures_with_mat_name_and_types: pytest.fixture
    ):
        m1_tex_1, m1_tex_2, m1_tex_3, m2_tex_1, m2_tex_2, m3_tex1, m3_tex2\
            = textures_with_mat_name_and_types
        checks_data = {
            'tex_paths': {
                self.first_mat: {
                    self.slot_to_check_1: m1_tex_1,
                    self.slot_to_check_2: m1_tex_2,
                    self.slot_to_check_3: m1_tex_3,
                },
                self.second_mat: {
                    self.slot_to_check_1: m2_tex_1,
                    self.slot_to_check_3: m2_tex_2,
                },
                self.third_mat: {
                    self.slot_to_check_1: m3_tex1,
                    self.slot_to_check_3: m3_tex2,
                }
            },
            'input_file': default_fbx_ascii_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Texture file names do not follow the recommended convention',
            'identifier': 'recommendedTexturesNaming',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Found {found}: {item}',
                    'found': 'inconsistent texture type',
                    'item': [
                        'M_5_123_Albedo.png',
                        'M_2_3_AO.png',
                        'M_5_123_AmbientOcclusion.png'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'inconsistent capitalization, most common in scene is CamelCase',
                    'item': [
                        'M_2_3_BASECOLOR.png',
                        'M_42_normal.png'
                    ]
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'texture': [
                {
                    'name': 'M_2_3_AO.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_2_3_BASECOLOR.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_2_3_Emission.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_42_BaseColor.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_42_normal.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_5_123_Albedo.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_5_123_AmbientOcclusion.png',
                    'complies_with_conventions': False
                }
            ]
        }

    @pytest.mark.parametrize(
        'textures_with_mat_name_and_types', [
            {
                first_mat: ['not_valid_type', 'AO', 'Emission'],
                second_mat: ['Albedo', ''],
            }
        ], indirect=True
    )
    def test_textures_naming_convention_incorrect_types_material_name_unused_files_fails(
        self,
        default_fbx_ascii_file,
        create_texture_with_incorrect_name,
        textures_with_mat_name_and_types: pytest.fixture
    ):
        m1_tex_1, m1_tex_2, m1_tex_3, m2_tex1, m2_tex2 = textures_with_mat_name_and_types
        checks_data = {
            'tex_paths': {
                self.first_mat: {
                    self.slot_to_check_1: m1_tex_1,
                    self.slot_to_check_2: m2_tex1,
                    self.slot_to_check_3: m1_tex_3,
                },
                self.second_mat: {
                    self.slot_to_check_1: default_fbx_ascii_file,
                    self.slot_to_check_2: m2_tex2,
                    self.slot_to_check_3: create_texture_with_incorrect_name,
                }
            },
            'input_file': default_fbx_ascii_file,
        }
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec, checks_data=checks_data
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Texture file names do not follow the recommended convention',
            'identifier': 'recommendedTexturesNaming',
            'msg_type': 'error',
            'items': [
                {
                    'message': 'Found {found}: {item}',
                    'found': 'unused textures',
                    'item': [
                        'M_2_3_AO.png'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'incorrect texture name connected to material M_2_3',
                    'item': [
                        'M_2_3_not_valid_type.png',
                        'M_5_123_Albedo.png'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'incorrect extension',
                    'item': [
                        'default_fbx_binary_file.fbx'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'incorrect texture name connected to material M_5_123',
                    'item': [
                        'default_fbx_binary_file.fbx'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'incorrect texture type ',
                    'item': [
                        'M_5_123_.png'
                    ]
                },
                {
                    'message': 'Found {found}: {item}',
                    'found': 'texture name should contain {Material_name}_{Texture type}',
                    'item': [
                        'textureName.png'
                    ]
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'texture': [
                {
                    'name': 'M_2_3_AO.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_2_3_Emission.png',
                    'complies_with_conventions': True
                },
                {
                    'name': 'M_2_3_not_valid_type.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_5_123_.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'M_5_123_Albedo.png',
                    'complies_with_conventions': False
                },
                {
                    'name': 'textureName.png',
                    'complies_with_conventions': False
                }
            ]
        }


class TestConsistentNaming:
    _check_key = 'consistentNaming'
    checks_spec = deepcopy(checks_spec_disabled)
    checks_spec[_check_key] = {
        'enabled': True,
        'type': 'error',
    }

    @pytest.mark.parametrize(
        'expected_ending_type, expected_ending, names',
        [
            ('prefix', 'mesh_box', ['mesh_box', 'mesh_box02', 'mesh_box03']),
            ('prefix', 'fa', [
                'faukkkbo_abc', 'fajkkkoo_abc', 'fazkkkoo_dbc', 'fatkkknordbc'
            ]),
            ('prefix', 'm', ['mat_a', 'mat_b', 'mat_c', 'mt_a', 'mt_b', 'mt_c']),
            ('suffix', '_MAT', ['wood_MAT', 'mat_b_MAT', 'mat_c_MAT', 'a_MAT', 'mt_c']),
            ('prefix', 'mat_', ['mat_wood', 'mat_glass', 'wood_MAT', 'glass_MAT']),
            ('prefix', 'mat', ['material_wood', 'mat_glass', 'material_wood', 'mat_wood']),
            ('suffix', '_wood', ['material_wood', 'MAT_glass', 'material_wood', 'MAT_wood']),
            ('prefix', 'material_', ['material_wood', 'MAT_glass', 'material_ice', 'MAT_wall']),
            (None, None, ['cube_a', 'glass', 'wood']),
            (None, None, ['cube_a']),
            (None, None, [])
        ]
    )
    def test_consistent_naming_most_common_ending(
        self,
        expected_ending_type,
        expected_ending,
        names,
    ):
        ending_type, ending = CheckConsistentNaming.get_most_common_ending(names)
        assert expected_ending_type is None or expected_ending_type == ending_type.name.lower()
        assert expected_ending == ending

    @pytest.mark.parametrize(
        'call_fixture_scene_with_named_entities', [
            {
                'meshes': ['mesh_box', 'mesh_box02', 'mesh_box03'],
                'empties': ['helper'],
                'materials': ['mat_a', 'mat_b', 'mat_c']
            }
        ], indirect=True
    )
    def test_consistent_naming_passes(
        self,
        call_fixture_scene_with_named_entities,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec
        )
        runner.runall()
        assert runner.passed is True
        assert runner.format_reports() == []
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'names': [
                {
                    'id': 0,
                    'entity_type': 'materials',
                    'consistent_naming': True
                },
                {
                    'id': 1,
                    'entity_type': 'materials',
                    'consistent_naming': True
                },
                {
                    'id': 2,
                    'entity_type': 'materials',
                    'consistent_naming': True
                },
                {
                    'id': 0,
                    'entity_type': 'geometry',
                    'consistent_naming': True
                },
                {
                    'id': 1,
                    'entity_type': 'geometry',
                    'consistent_naming': True
                },
                {
                    'id': 2,
                    'entity_type': 'geometry',
                    'consistent_naming': True
                },
                {
                    'id': 0,
                    'entity_type': 'helpers',
                    'consistent_naming': True
                }
            ]
        }

    @pytest.mark.parametrize(
        'call_fixture_scene_with_named_entities', [
            {
                'meshes': ['cube_a', 'glass'],
                'empties': ['helper', 'lorem'],
                'materials': ['mat_a', 'iron']
            }
        ], indirect=True
    )
    def test_consistent_naming_no_common_prefix_fails(
        self,
        call_fixture_scene_with_named_entities,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Naming should be consistent and use common prefix or suffix',
            'identifier': 'consistentNaming',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{found}: {item}',
                    'found': 'No common prefix or suffix for materials',
                    'item': ['iron', 'mat_a']
                },
                {
                    'message': '{found}: {item}',
                    'found': 'No common prefix or suffix for geometry',
                    'item': ['cube_a', 'glass']
                },
                {
                    'message': '{found}: {item}',
                    'found': 'No common prefix or suffix for helpers',
                    'item': ['helper', 'lorem']
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'names': [
                {
                    'id': 0,
                    'entity_type': 'materials',
                    'consistent_naming': False
                },
                {
                    'id': 1,
                    'entity_type': 'materials',
                    'consistent_naming': False
                },
                {
                    'id': 0,
                    'entity_type': 'geometry',
                    'consistent_naming': False
                },
                {
                    'id': 1,
                    'entity_type': 'geometry',
                    'consistent_naming': False
                },
                {
                    'id': 0,
                    'entity_type': 'helpers',
                    'consistent_naming': False
                },
                {
                    'id': 1,
                    'entity_type': 'helpers',
                    'consistent_naming': False
                }
            ]
        }

    @pytest.mark.parametrize(
        'call_fixture_scene_with_named_entities', [
            {
                'meshes': ['cubea', 'cubeb', 'Cube_c'],
                'empties': [],
                'materials': ['__iron_wood_MAT', 'iron_material', 'mat_material']
            }
        ], indirect=True
    )
    def test_consistent_naming_inconsistent_names_fails(
        self,
        call_fixture_scene_with_named_entities,
    ):
        runner = cgtcheck.runners.CheckRunner(
            checks_spec=self.checks_spec
        )
        runner.runall()
        assert runner.passed is False
        assert runner.format_reports() == [{
            'message': 'Naming should be consistent and use common prefix or suffix',
            'identifier': 'consistentNaming',
            'msg_type': 'error',
            'items': [
                {
                    'message': '{found}: {item}',
                    'found': 'Inconsistent naming for materials, '
                             'most common suffix in the scene is "_material"',
                    'item': ['__iron_wood_MAT']
                },
                {
                    'message': '{found}: {item}',
                    'found': 'Inconsistent naming for geometry, '
                             'most common prefix in the scene is "cube"',
                    'item': ['Cube_c']
                }
            ]
        }]
        this_check = next(check for check in runner.checks if check.key == self._check_key)
        assert this_check.format_properties() == {
            'names': [
                {
                    'id': 0,
                    'entity_type': 'materials',
                    'consistent_naming': False
                },
                {
                    'id': 1,
                    'entity_type': 'materials',
                    'consistent_naming': True
                },
                {
                    'id': 2,
                    'entity_type': 'materials',
                    'consistent_naming': True
                },
                {
                    'id': 0,
                    'entity_type': 'geometry',
                    'consistent_naming': False
                },
                {
                    'id': 1,
                    'entity_type': 'geometry',
                    'consistent_naming': True
                },
                {
                    'id': 2,
                    'entity_type': 'geometry',
                    'consistent_naming': True
                }
            ]
        }
