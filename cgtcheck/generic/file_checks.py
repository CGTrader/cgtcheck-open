# This code is part of KODAMA Tool - a helper script/plug-in which helps validate that the
# currently opened model meets acceptance criteria defined in CGTrader platforms, and
# once all criteria are met allows to package the model and its textures and upload them to
# corresponding platform page.
#
# This code is provided to you by UAB CGTrader, code 302935696, address - Antakalnio str. 17,
# Vilnius, Lithuania, the company registered with the Register of Legal Entities of the Republic
# of Lithuania (CGTrader).
#
# Copyright (C) 2022  CGTrader.
#
# If you obtain this program as a plug-in for Blender, this program is provided to you as free
# software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. It is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have
# received a copy of the GNU General Public License along with this program.  If not, see
# https://www.gnu.org/licenses/.
#
# If you obtain this program as a plug-in for 3ds Max, it is proprietary software of CGTrader and
# you are given a licence to use the program in accordance with the End User Licence Agreement.
# The text of the licence is included into the package as 3DSMAX_LICENCE.
import enum
import os
import logging
from collections import defaultdict, Counter
from pathlib import Path
from typing import Tuple, List, Dict, Union, NamedTuple, Generator
from itertools import chain

from threed.common.formats import fbx_version
from cgtcheck.common import Check, Properties
from cgtcheck.runners import CheckRunner


logger = logging.getLogger(__name__)


@CheckRunner.register
class CheckMultipleFileFormats(Check, Properties):
    """
    Check if number of images meet multiple file format requirement.
    """

    key = 'multipleFileFormats'
    version = (0, 1, 1)

    def run(self) -> List[str]:
        """
        Return a list of files which don't have their counterparts for all extensions.
        Extensions are specified in check specification: {"parameters": {"formats": []}}
        """
        input_file = self.collector.input_file or ''
        file_formats = self.params.get('parameters', {}).get('formats', ())
        if not input_file or not file_formats:
            self.failures = []
            return self.failures

        file_paths = self._get_filepaths_by_extension(
            Path(input_file).parent, tuple(file_formats)
        )

        formats_per_base_name = defaultdict(set)
        for file_path in file_paths:
            formats_per_base_name[file_path.stem].add(file_path.suffix.strip('.'))

        self.properties = [
            {'name': k, 'formats': sorted(v)} for k, v in formats_per_base_name.items()
        ]

        self.failures = []
        file_formats = set(file_formats)
        for base_name in formats_per_base_name:
            missing_formats = file_formats - formats_per_base_name[base_name]
            sorted_missing_formats = sorted(missing_formats, key=str.lower)
            for missing_format in sorted_missing_formats:
                self.failures.append(f'{base_name}.{missing_format}')

        self.failures.sort()
        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check.
        """
        return ["{}".format(missing_file) for missing_file in self.failures]

    def format_failure(self, failure: str) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
            'expected': True,
            'found': None,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        file_formats = self.params.get('parameters', {}).get('formats', ())
        return self.metadata.check_description.format(', '.join(file_formats))

    @staticmethod
    def _get_filepaths_by_extension(
        start_dir: Path,
        extensions: Tuple[str]
    ) -> List[Path]:
        """
        Get all file paths with specified extensions from start directory and its subdirectories.
        """
        file_paths = []
        for path in start_dir.glob('**/*'):
            if path.is_file() and path.suffix.lower().endswith(extensions):
                file_paths.append(path)

        return file_paths


@CheckRunner.register
class CheckUnusedTextures(Check, Properties):
    """
    Check if all supplied textures are used.
    """

    key = 'unusedTextures'
    version = (0, 1, 0)

    def run(self) -> List[str]:
        """
        Return a list of texture files not assigned to materials
        """
        tex_paths = self.collector.mat_texture_path
        input_file = self.collector.input_file or ''
        formats = self.params.get('parameters', {}).get('formats', {})

        tex_in_spec = {tex_path for mat in tex_paths.values() for tex_path in mat.values()}
        file_paths = self._get_filepaths_by_extension(os.path.dirname(input_file), tuple(formats))
        self.failures = list(tex for tex in file_paths if tex not in tex_in_spec)

        self.properties = [
            {'name': os.path.basename(tex), 'used': (tex in tex_in_spec)} for tex in file_paths
        ]

        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(file_path) for file_path in self.failures]

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': os.path.basename(failure),
        }

    @staticmethod
    def _get_filepaths_by_extension(
        path: str,
        extensions: Tuple[str]
    ) -> List[str]:
        """
        Get all file pahts with selected extensions from directory and its subdirectories.
        """
        file_paths = []

        for root, _dirs, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith(extensions):
                    file_paths.append(os.path.join(root, filename))

        return file_paths

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'textures': self.properties
        }


class CheckFbxFormatInfo(NamedTuple):
    """
    Record type for CheckFbxFormat failures
    """
    is_binary: bool
    version: int


@CheckRunner.register
class CheckFbxFormat(Check, Properties):
    """
    Check Fbx file format requirements. ASCII/binary and version.
    """

    key = 'fbxFormat'
    version = (0, 1, 1)

    failures: List[CheckFbxFormatInfo]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = {}
        self._allow_binary = None
        self._allow_ascii = None
        self._version_min = None
        self._version_max = None

    def run(self) -> List[CheckFbxFormatInfo]:
        """
        Return a list of texture files not assigned to materials
        """
        input_file = self.collector.input_file
        if not input_file:
            logger.warning("fbxFormat will skip; check requires 'collector.input_file' to be set")
            return self.failures

        if os.path.splitext(input_file)[1].lower() != '.fbx':
            logger.warning('File is not FBX, fbxFormat will skip: %s', input_file)
            self.properties = {'type': None, 'version': None}
            return self.failures

        parameters = self.params.get('parameters', {})
        allow_binary = self._allow_binary = parameters.get('allow_binary', True)
        allow_ascii = self._allow_ascii = parameters.get('allow_ascii', False)
        if not (allow_ascii or allow_binary):
            raise ValueError('Either binary or ASCII type needs to be allowed for check to pass')

        version_parameters = parameters.get('version', {})
        version_min = self._version_min = version_parameters.get('min', 7100)
        version_max = self._version_max = version_parameters.get('max', None)

        fbx_info = CheckFbxFormatInfo(*fbx_version(input_file))
        self.properties = {
            'type': self._binary_to_name(fbx_info.is_binary),
            'version': fbx_info.version,
        }

        meets_binary_req = allow_binary or not fbx_info.is_binary
        meets_ascii_req = allow_ascii or fbx_info.is_binary
        if not (meets_binary_req and meets_ascii_req):
            self.failures.append(fbx_info)
        elif (version_min is not None and fbx_info.version < version_min) \
                or (version_max is not None and fbx_info.version > version_max):
            self.failures.append(fbx_info)

        return self.failures

    @staticmethod
    def _binary_to_name(is_binary: bool) -> str:
        return 'binary' if is_binary else 'ASCII'

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return [
            f'{self._binary_to_name(failure.is_binary).capitalize()} FBX, version {failure.version}'
            for failure in self.failures
        ]

    def format_failure(self, failure: CheckFbxFormatInfo) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        allowed_types = []
        if self._allow_binary:
            allowed_types.append(self._binary_to_name(True))
        if self._allow_ascii:
            allowed_types.append(self._binary_to_name(False))
        return {
            'message': self.metadata.item_msg,
            'expected_type': ' or '.join(allowed_types),
            'expected_version_min': self._version_min,
            'expected_version_max': self._version_max,
            'found_type': self._binary_to_name(failure.is_binary),
            'found_version': failure.version,
        }

    def format_properties(self) -> Dict[str, Union[str, int]]:
        """
        Format a property report.
        """
        return self.properties


@CheckRunner.register
class CheckRecommendedTexturesNaming(Check, Properties):
    """
    Check if the texture file names follow the recommended convention,
    {Material}_{Texture type}.{file_format}.
    """

    key = 'recommendedTexturesNaming'
    version = (0, 1, 0)
    allowed_types = {
        'BaseColor': ['BaseColor', 'Albedo'],
        'Metalness': ['Metalness', 'Metallic'],
        'Roughness': ['Roughness'],
        'Normal': ['Normal'],
        'AmbientOcclusion': ['AmbientOcclusion', 'Ambient', 'AO'],
        'Opacity': ['Opacity'],
        'Emissive': ['Emission', 'Emissive'],
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, List[str]] = {}
        self.properties: List[dict[str, str]] = {}

    def run(self) -> Dict[str, List[str]]:
        """
        Return a dict with information about the type of error
        and textures that do not follow the convention
        Return information about texture for property reports
        """
        tex_paths = self.collector.mat_texture_path
        input_file = self.collector.input_file or ''
        tex_in_spec = {tex_path for mat in tex_paths.values() for tex_path in mat.values()}

        formats = self.params.get('parameters', {}).get('formats', {})
        allowed_ext = formats.get('allowed_ext', {})
        not_allowed_ext = formats.get('not_allowed_ext', {})

        all_textures = self._get_filepaths_by_extension(
            os.path.dirname(input_file), tuple(allowed_ext + not_allowed_ext)
        )
        textures_with_required_elements = {}
        unused_textures = list(texture for texture in all_textures if texture not in tex_in_spec)

        if unused_textures:
            self.failures.update({'unused textures': unused_textures})
        all_allowed_types = list(map(str.lower, chain(*self.allowed_types.values())))
        for mat_name, connected_textures in tex_paths.items():
            for texture_path in connected_textures.values():
                texture_name, texture_ext = os.path.splitext(os.path.basename(texture_path))
                if not texture_ext.lower().endswith(tuple(allowed_ext)):
                    self.failures.setdefault('incorrect extension', []).append(texture_path)

                texture_name_elements = texture_name.rsplit('_', 1)
                if len(texture_name_elements) != 2:
                    self.failures.setdefault(
                        'texture name should contain {Material_name}_{Texture type}', []
                    ).append(texture_path)
                    continue

                if texture_name_elements[0] != mat_name:
                    self.failures.setdefault(
                        f'incorrect texture name connected to material {mat_name}', []
                    ).append(texture_path)
                    continue

                if texture_name_elements[1].lower() not in all_allowed_types:
                    self.failures.setdefault(
                        f'incorrect texture type {texture_name_elements[1]}', []
                    ).append(texture_path)
                    continue

                textures_with_required_elements.update({texture_path: texture_name_elements[1]})
        self._check_type_consistency(textures_with_required_elements)
        self._check_capitalization_consistency(textures_with_required_elements)

        self.properties = [
            {
                'name': os.path.basename(tex),
                'complies_with_conventions': (
                    tex not in chain(*self.failures.values())
                )
            }
            for tex in all_textures
        ]
        return self.failures

    def _check_type_consistency(self, textures_with_required_elements: Dict[str, str]) -> None:
        """
        In the allowed_types dict, we have a list of allowed values for each texture type.
        E.g. 'BaseColor': ['BaseColor', 'Albedo'], we need to check if all texture file names
        use the same value in a given texture type, e.g. all use 'BaseColor'.
        If not, less common texture types will be added to Failures

        Args:
            textures_with_required_elements (dict): strings with texture path and with texture type.
        """
        variants_to_check = []
        type_counts = Counter(textures_with_required_elements.values())
        for allowed_variants in self.allowed_types.values():
            if len(allowed_variants) > 1:
                for variant in allowed_variants:
                    if variant.lower() in map(str.lower, textures_with_required_elements.values()):
                        variants_to_check.append(variant)

                if len(variants_to_check) > 1:
                    most_common_type, _count = type_counts.most_common()[0]
                    for texture, tex_type in textures_with_required_elements.items():
                        if tex_type.lower() != most_common_type.lower() and \
                                tex_type.lower() in map(str.lower, variants_to_check):
                            self.failures.setdefault(
                                'inconsistent texture type', []
                            ).append(texture)
                variants_to_check.clear()

    def _check_capitalization_consistency(
        self,
        textures_with_required_elements: Dict[str, str]
    ) -> bool:
        """
        All texture types e.g 'BaseColor', 'AmbientOcclusion' in the texture name
        should use the same capitalization e.g. all CamelCase
        If not, textures with less common capitalization will be added to Failures

        Args:
            textures_with_required_elements (dict): strings with texture path and with texture type.
        """
        case_count = {}
        unique_texture_types = set(textures_with_required_elements.values())

        allowed_types_camel_case = set(chain(*self.allowed_types.values()))
        is_all_camel_case = unique_texture_types.issubset(allowed_types_camel_case)
        if is_all_camel_case:
            return is_all_camel_case
        case_count['CamelCase'] = [
            word for word in textures_with_required_elements.values()
            if word in chain(*self.allowed_types.values())
        ]

        is_all_upper = all(word.isupper() for word in unique_texture_types)
        if is_all_upper:
            return is_all_upper
        case_count['UPPER'] = [
            tex_type for tex_type in textures_with_required_elements.values() if tex_type.isupper()
        ]

        is_all_lower = all([(word.islower()) for word in unique_texture_types])
        if is_all_lower:
            return is_all_lower
        case_count['lower'] = [
            tex_type for tex_type in textures_with_required_elements.values() if tex_type.islower()
        ]

        is_all_capitalize = all(
            [tex_type.capitalize() == tex_type for tex_type in unique_texture_types]
        )
        if is_all_capitalize:
            return is_all_capitalize
        case_count['Capitalize'] = [
            tex_type for tex_type in textures_with_required_elements.values()
            if tex_type.capitalize() == tex_type
        ]
        most_common_case = max(case_count, key=lambda x: len(set(case_count[x])))
        for texture, tex_type in textures_with_required_elements.items():
            if tex_type not in case_count[most_common_case]:
                self.failures.setdefault(
                    f'inconsistent capitalization, most common in scene is {most_common_case}',
                    []
                ).append(texture)

        return False

    def get_failures(self) -> Generator[Tuple[str, List[str]], None, None]:
        """
        Return an iterator of failures.
        """
        return ((failure_type, textures) for failure_type, textures in self.failures.items())

    def format_failure(self, failure: Tuple) -> Dict[str, Union[str, str]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        failure_type, textures = failure

        return {
            'message': self.metadata.item_msg,
            'found': failure_type,
            'item': [os.path.basename(texture) for texture in textures],
        }

    @staticmethod
    def _get_filepaths_by_extension(
        path: str,
        extensions: Tuple[str]
    ) -> List[str]:
        """
        Get all file paths with selected extensions from directory and its subdirectories.
        """
        file_paths = []

        for root, _dirs, files in os.walk(path):
            for filename in files:
                if filename.lower().endswith(extensions):
                    file_paths.append(os.path.join(root, filename))

        return file_paths

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }


class EndingType(enum.Enum):
    """
    Defines endings
    """
    PREFIX = 0
    SUFFIX = 1


@CheckRunner.register
class CheckConsistentNaming(Check, Properties):
    """
    Check that the naming structure in all materials, geometries and empty objects is consistent
    the same suffix or prefix should be present in the names.
    Material names example:
        Incorrect:
            Material_glass
            M_metal
            Mat_Wood
            Plastic_material
        Correct:
            M_glass
            M_metal
            M_Wood
            M_material
    """

    key = 'consistentNaming'
    version = (0, 1, 0)
    ending_methods = {
        EndingType.PREFIX: str.startswith,
        EndingType.SUFFIX: str.endswith,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, List[str]] = {}

    def run(self) -> Dict[str, List[str]]:
        """
        Report inconsistent names per group of entities.
        Report those that do not have the most common prefix/suffix.
        Report all names if there is no common prefix/suffix.
        Report nothing if only one element exists in a given collector.
        Return information about the names in the collectors for property reports
        """

        names_collection = {
            'materials': [mat.name for mat in self.collector.materials],
            'geometry': [mat.name for mat in self.collector.objects],
            'helpers': [mat.name for mat in self.collector.empties]
        }

        for collection, names in names_collection.items():
            if not names:
                continue
            if len(names) <= 1:
                self.properties.append(
                    {
                        'id': 0,
                        'entity_type': collection,
                        'consistent_naming': True
                    }
                )
                continue

            ending_type, ending = self.get_most_common_ending(names)
            for i, name in enumerate(names):
                if ending_type:
                    consistent_naming = True
                    if not self.ending_methods[ending_type](name, ending):
                        consistent_naming = False
                        self.failures.setdefault(
                            f'Inconsistent naming for {collection}, most common '
                            f'{ending_type.name.lower()} in the scene is "{ending}"',
                            []
                        ).append(name)
                else:
                    self.failures.setdefault(
                        f'No common prefix or suffix for {collection}',
                        []
                    ).append(name)
                    consistent_naming = False
                self.properties.append(
                    {
                        'id': i,
                        'entity_type': collection,
                        'consistent_naming': consistent_naming
                    }
                )

        return self.failures

    @staticmethod
    def get_most_common_ending(
        names: List[str]
    ) -> Union[Tuple[EndingType, str],  Tuple[None, None]]:
        """
        Returns most common ending (prefix or suffix) from names
        If most common prefix and most common suffix occur same number of times,
        the prefix is returned.

        Args:
            names: list with objects, empties or material names
        Returns:
            [0] EndingType value indicating whether a 'suffix' or 'prefix' was returned
            [1] value of the suffix or prefix
            Both elements returned as None indicate that there is no common prefix or suffix.
        """
        def find_common_prefixes(words, level, results):
            letters = defaultdict(list)
            for w in words:
                if level < len(w):
                    letters[w[level]].append(w)

            for group_of_words in letters.values():
                if len(group_of_words) > 1:
                    find_common_prefixes(group_of_words, level + 1, results)

            if level != 0:
                results.append((words[0][:level], len(words)))

            return

        prefixes = []
        find_common_prefixes(names, 0, prefixes)
        max_prefix = max(prefixes, default=None, key=lambda item: (item[1], len(item[0])))

        suffixes = []
        inverted_names = [w[::-1] for w in names]
        find_common_prefixes(inverted_names, 0, suffixes)
        max_suffix_reversed = max(suffixes, default=None, key=lambda item: (item[1], len(item[0])))

        if (max_prefix and max_suffix_reversed) and (max_suffix_reversed[1] > max_prefix[1]):
            return EndingType.SUFFIX, max_suffix_reversed[0][::-1]
        elif max_prefix:
            return EndingType.PREFIX, max_prefix[0]
        elif max_suffix_reversed:
            return EndingType.SUFFIX, max_suffix_reversed[0][::-1]
        else:
            return None, None

    def get_failures(self) -> Generator[Tuple[str, List[str]], None, None]:
        """
        Return an iterator of failures.
        """
        return ((failure_type, textures) for failure_type, textures in self.failures.items())

    def format_failure(self, failure: Tuple) -> Dict[str, Union[str, str]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        failure_type, textures = failure

        return {
            'message': self.metadata.item_msg,
            'found': failure_type,
            'item': [os.path.basename(texture) for texture in textures],
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'names': self.properties
        }
