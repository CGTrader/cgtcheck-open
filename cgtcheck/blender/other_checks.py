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

from __future__ import annotations

import re
import os
import logging
import operator
from contextlib import contextmanager
from typing import Sequence, Tuple, List, Dict, Iterator, Set, Union, Generator
from math import sqrt, log, floor, radians, degrees
from collections import Counter, namedtuple
from dataclasses import dataclass

import bpy
import bmesh
from bpy.types import Object, Material, Mesh
from bpy_extras import mesh_utils
from mathutils import Vector, Euler

from PIL import Image

import threed.blender.dimensions as dimensions
import threed.blender.uv as uv
import threed.blender.common as bcommon

import cgtcheck
from cgtcheck.common import Check, Properties
from cgtcheck.blender.collector import BlenderEntityCollector

from cgttex import TexPatterns, ParseError
from cgttex.multi import MultiTexPatterns


logger = logging.getLogger(__name__)


def more_readable_re(regex: str) -> str:
    """
    Takes in regex word and replaces or removes regex symbols so the output would be
    more comprehensible. Intended to be used in cases like user-error output text formatting.
    """
    replaces = {
        "(": "",
        ")": "",
        "^": "",
        "$": "",
        r".\w+": "",
        r"\w+": "(letters)",
        r"\w": "(letter)",
        r"\d+": "(digit)",
        r"\d": "(digit)",
    }
    for repl_from, repl_to in replaces.items():
        regex = regex.replace(repl_from, repl_to)
    return regex


class TexelDensityMixin:

    @dataclass
    class FailureInfo:
        """
        Holds information about a single failed object
        """

        mesh: Mesh
        issue: str
        expected: Union[float, None]
        found: Union[float, None]

        def format_simple(self) -> str:
            """
            Returns a simple message representing this issue,
            similar to what was used in old error reports.
            """
            if self.issue == 'density':
                return (
                    f'expected: {self.expected:.4f} px/cm, found: {self.found:.4f} '
                    f'px/cm (object: {self.mesh.name}) '
                )
            elif self.issue == 'contains no UVs':
                return f'{self.issue} (object: {self.mesh.name})'
            raise ValueError(f'Unrecognized texel density issue type: {self.issue}')

    def _check_material_texel_density(
        self,
        material: Material,
        mesh_objects: Sequence[Object],
        collector: BlenderEntityCollector,
        width: int,
        height: int,
        expected_density: float = None,
        threshold: float = 0.1
    ) -> Tuple[List[FailureInfo], List[Dict]]:
        """
        Check texel density of given material, return failed objects with texel density info.

        Note that the incorrect texel density can be either lower or higher than expected.

        Args:
            material: Material which textures are being checked.
            mesh_objects: The list of bpy_types.Mesh objects being checked.
            collector: Collector to iterate through collected materials,
            width: Horizontal dimension of a reference texture.
            height: Vertical dimension of a reference texture.
            expected_density: Expected texel density of single dimension in tx/m.
            threshold: Allowed texel density deviation.

        Returns:
            Failed objects paired with their texel density information.
            Properties report with texel density per object and material id.
        Raises:
            ValueError: If expected_density is equal to zero.
        Collect texel density per object and material id for properties report.
        """

        def texel_info_to_pxcm(expected: float, found: float) -> Dict[str, float]:
            return {'expected': expected * 0.01, 'found': found * 0.01}

        if expected_density == 0.0:
            raise ValueError('Expected texel density must not be 0')

        px_per_uv_area = width * height
        failures = []
        uv_layer_id = 0
        properties = []
        unit_scale_sq = bpy.context.scene.unit_settings.scale_length ** 2
        for i, obj in enumerate(mesh_objects):
            materials_name_id = {
                mat.name: collector.materials.index(mat)
                for mat in obj.data.materials if mat is not None
            }
            scale_sq = (sum(obj.scale) / 3) ** 2  # area increases quadratically with scale
            if scale_sq == 0.0:
                logger.warning('Ignoring object with 0 scale for texel density check: ' + obj.name)
                continue

            mesh = obj.data
            mtl_id = bcommon.material_index(mesh, material)
            if mtl_id == -1:
                continue

            # Report meshes without UVs also
            if len(mesh.uv_layers) == 0:
                failures.append(
                    self.FailureInfo(mesh=obj, issue='contains no UVs', expected=True, found=None)
                )
                continue

            for shell in mesh_utils.mesh_linked_uv_islands(mesh):
                mtl_shell = [f for f in shell if mesh.polygons[f].material_index == mtl_id]

                if len(mtl_shell) == 0:
                    continue  # No specified material in the shell

                geo_area = sum(mesh.polygons[f].area for f in mtl_shell)
                uv_area = uv.uv_faces_area(mtl_shell, mesh, uv_layer_id)

                if geo_area == 0.0:
                    continue

                px_per_geo_m2 = px_per_uv_area * uv_area / (geo_area * scale_sq * unit_scale_sq)
                density = sqrt(px_per_geo_m2)
                properties.append(
                    {
                        'id': i,
                        'material': materials_name_id[material.name_full],
                        'density': density * 0.01
                    }
                )

                if expected_density is not None:
                    if abs(expected_density - density) / max(expected_density, density) > threshold:
                        failures.append(
                            self.FailureInfo(
                                mesh=obj,
                                issue='density',
                                **texel_info_to_pxcm(expected_density, density),
                            )
                        )
                        break

        return failures, properties


@cgtcheck.runners.CheckRunner.register
class CheckTexelDensity(Check, Properties, TexelDensityMixin):
    """
    Check object's texel density of mesh objects against the expected value.
    """

    FailureInfo = TexelDensityMixin.FailureInfo

    key = 'texelDensity'
    version = (0, 1, 4)
    failures: Dict[Material, List[FailureInfo]] = {}
    format_properties = Properties._basic_format_properties

    def run(self) -> Dict[Material, List[FailureInfo]]:
        """
        Return a dict of failed materials with failure messages.
        """
        check_params = self.params.get('parameters', {})

        self.failures, self.properties = self._check_texel_density(
            self.collector.objects,
            self.collector.mat_texture_path,
            check_params["expected_density"],
            allowed_deviation=check_params.get("density_deviation", 0.1),
            tex_type='color',
            mtl_ignores=check_params.get("ignore_materials", ()),
        )
        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return [
            f'{mat.name}: {failure_info.format_simple()}'
            for mat, failure_info in self.get_failures()
        ]

    def get_failures(self) -> Iterator[Tuple[Material, FailureInfo]]:
        """
        Return an iterator of failures.
        One Material entry per its object failure, instead of mapping of materials to failures.
        """
        return (
            (mat, failure)
            for mat, failures in self.failures.items()
            for failure in failures
        )

    def format_failure(self, failure: Tuple[Material, FailureInfo]) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        material, fail_info = failure
        report = {
            'message': self.metadata.item_msg[fail_info.issue],
            'item': fail_info.mesh.name,
            'expected': fail_info.expected,
            'found': fail_info.found,
        }
        if fail_info.issue == 'density':
            report['material'] = material.name_full
        return report

    def _check_texel_density(
        self,
        mesh_objects: Sequence[Object],
        tex_paths_all: Dict[Object, Dict[str, str]],
        expected_density: float,
        allowed_deviation: float = 0.1,
        tex_type: str = 'color',
        mtl_ignores: Dict[str, str] = ()
    ) -> Tuple[Dict[Material, List[FailureInfo]], List[Dict]]:
        """
        Check texel density of mesh objects, return failed materials with failure messages
        and properties report with texel density per object and material id.

        Args:
            mesh_objects: The list of bpy_types.Mesh objects being checked.
            tex_paths_all: Path to textures.
            expected_density: Expected texel density of single dimension in tx/m.
            allowed_deviation: Allowed texel density deviation.
            tex_type: Type of texture
            mtl_ignores: Materials that should not be checked.
        """
        failures_by_mat: Dict[Material, List[self.FailureInfo]] = {}
        properties = []

        if mtl_ignores:
            mtl_ignores = [re.compile(regex) for regex in mtl_ignores]
        for mtl in self.collector.materials:
            if mtl is None:
                continue

            if any(regex.match(mtl.name) for regex in mtl_ignores):
                logger.warning("Material explicitly ignored for texel density check: %s", mtl.name)
                continue

            tex_path = tex_paths_all.get(mtl.name, {}).get(tex_type, None)
            if tex_path is not None:
                if not os.path.exists(tex_path):
                    logger.warning('Not found on disk, skipping: %s', tex_path)
                    continue
                with Image.open(tex_path) as image:
                    failures, properties = self._check_material_texel_density(
                        material=mtl,
                        mesh_objects=mesh_objects,
                        collector=self.collector,
                        width=image.width,
                        height=image.height,
                        expected_density=expected_density,
                        threshold=allowed_deviation
                    )

                    if failures:
                        failures_by_mat[mtl] = failures
            else:
                logger.warning(
                    "No texture of type '%s' found for material '%s'. "
                    "Texel density check for the material will be skipped",
                    tex_type, mtl.name
                )

        return failures_by_mat, properties

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        expected_density = self.params.get('parameters', {}).get('expected_density', ())
        return self.metadata.check_description.format(expected_density)


@cgtcheck.runners.CheckRunner.register
class CheckInconsistentTexelDensity(
    Check, Properties, TexelDensityMixin
):
    """
    Check that mesh objects' texel density is consistent.
    """

    FailureInfo = TexelDensityMixin.FailureInfo

    key = 'inconsistentTexelDensity'
    version = (0, 1, 2)
    failures: List[Tuple[float, float, float]] = []
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[float, float, float]]:
        """
        Return a dict of failed materials with failure messages.
        """
        check_params = self.params.get('parameters', {})

        self.failures, self.properties = self.check_density_is_consistent(
            allowed_density_deviation=check_params.get("density_deviation", 0.1),
            mtl_ignores=check_params.get("ignore_materials", ()),
        )
        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return [
            f'Min density: {min_density}, max density: {max_density}, '
            f'density deviation: {density_deviation}'
            for min_density, max_density, density_deviation in self.get_failures()
        ]

    def format_failure(
        self,
        failure: Tuple[float, float, float]
    ) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        min_density, max_density, density_deviation = failure
        report = {
            'message': self.metadata.item_msg,
            'min_density': round(min_density, 3),
            'max_density': round(max_density, 3),
            'expected': self.params.get('parameters', {}).get('density_deviation', 0.1),
            'found': density_deviation,
        }
        return report

    def check_density_is_consistent(
        self,
        allowed_density_deviation=0.1,
        mtl_ignores=()
    ):
        """
        Checks that texel density is consistent
        By checking that it does not exceed "allowed_density_deviation"
        """
        failures = []
        properties = []

        mesh_objects = self.collector.objects
        tex_paths_all = self.collector.mat_texture_path

        if mtl_ignores:
            mtl_ignores = [re.compile(regex) for regex in mtl_ignores]

        for mat in self.collector.materials:
            if mat is None:
                continue

            if any(regex.match(mat.name) for regex in mtl_ignores):
                logger.warning("Material explicitly ignored for texel density check: %s", mat.name)
                continue

            width, height = 4096, 4096
            tex_path = tex_paths_all.get(mat.name, {}).get('color', None)
            if tex_path is not None:
                if not os.path.exists(tex_path):
                    logger.warning('Not found on disk, skipping: %s', tex_path)
                    continue
                with Image.open(tex_path) as image:
                    width, height = image.width, image.height

            _, found_properties = self._check_material_texel_density(
                material=mat,
                mesh_objects=mesh_objects,
                collector=self.collector,
                width=width,
                height=height
            )
            properties.extend(found_properties)

        densities_only = [p['density'] for p in properties]
        if densities_only:
            density_max = max(densities_only)
            density_min = min(densities_only)
            density_deviation = abs(density_max - density_min)
            if density_deviation > allowed_density_deviation:
                failures = [(density_max, density_min, density_deviation)]

        return failures, properties


@cgtcheck.runners.CheckRunner.register
class CheckTextureResolution(Check, Properties):
    """
    Check materials for inconsistent texture resolution in materials.
    """

    @dataclass
    class FailureInfo:
        """
        Holds information about a single failed object
        """

        filename: str
        expected: Tuple[int, int]
        found: Tuple[int, int]

        def format_simple(self) -> str:
            """
            Returns a simple message representing this issue,
            similar to what was used in old error reports.
            """
            return f'{self.filepath} ({self.found[0]}x{self.found[1]})'

    key = 'inconsistentTexResInMaterial'
    version = (0, 1, 2)
    failures: Dict[Material, List[FailureInfo]] = {}
    format_properties = Properties._basic_format_properties

    def run(self) -> Dict[Material, List[FailureInfo]]:
        """
        Return a dict of failed materials with problematic texture's information.
        Collect texture name and resolution per object and material id for properties report.
        """
        self.failures = self._tex_resolution_consistency(
            self.collector.mat_texture_path
        )
        self.properties = self._tex_resolution_per_material(
            self.collector.mat_texture_path
        )
        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return [
            '{}: {}'.format(mat.name, ', '.join(fi.format_simple() for fi in failure_infos))
            for mat, failure_infos in self.failures.items()
        ]

    def get_failures(self) -> Iterator[Tuple[Material, FailureInfo]]:
        """
        Return an iterator of failures.
        One Material entry per its object failure, instead of mapping of materials to failures.
        """
        return (
            (mat, failure)
            for mat, failures in self.failures.items()
            for failure in failures
        )

    def format_failure(self, failure: Tuple[Material, FailureInfo]) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """

        material, fail_info = failure
        return {
            'message': self.metadata.item_msg,
            'material': material.name_full,
            'item': fail_info.filename,
            'expected': fail_info.expected,
            'found': fail_info.found,
        }

    def _tex_resolution_per_material(
        self,
        material_textures: Dict[str, Dict[str, str]]
    ) -> list[dict]:
        """
        Returns list of dictionary with object and material id, texture name and  resolutions.
        """
        properties = []
        for i, obj in enumerate(self.collector.objects):
            materials_name_id = {mat.name: self.collector.materials.index(mat) for
                                 mat in obj.data.materials if mat is not None}
            for material_name, textures in material_textures.items():
                if material_name not in materials_name_id.keys():
                    continue
                for filepath in textures.values():
                    if not os.path.exists(filepath):
                        logger.warning('Not found on disk, skipping: %s', filepath)
                        continue
                    with Image.open(filepath) as img:
                        properties.append(
                            {
                                'id': i,
                                'material': materials_name_id[material_name],
                                'texture_name': os.path.basename(filepath),
                                'resolution': [img.width, img.height],
                            }
                        )
        return properties

    @classmethod
    def _tex_resolution_consistency(
        cls,
        material_textures: Dict[str, Dict[str, str]]
    ) -> Dict[Material, List[FailureInfo]]:
        """
        Returns dictionary of materials which textures resolutions do not match.

        Material containing texture which resolution don't match material's most frequently
        used resolution is reported.

        Args:
            material_textures (dict(str, dict(str, str)))): Paths to texture files.
                material names assigned to filepaths paired with texture

        Returns:
            dict (object, str): Failed materials(bpy.types.Material)
                paired with list of failed tuples, each holding texture and its resolution
        """
        failed_materials = {}
        for material_name, textures in material_textures.items():
            if not textures:
                logger.warning(
                    "Material %s has no textures; skipping texture resolution consistency check",
                    material_name
                )
                continue

            elif len(textures) == 1:
                logger.warning(
                    "Material %s has one texture; skipping texture resolution consistency check",
                    material_name
                )
                continue

            # collect resolutions per texture
            tex_resolutions: Dict[str, Tuple[int, int]] = {}
            for filepath in textures.values():
                if not os.path.exists(filepath):
                    logger.warning('Not found on disk, skipping: %s', filepath)
                    continue
                with Image.open(filepath) as img:
                    tex_resolutions[filepath] = (img.width, img.height)

            if not tex_resolutions:
                continue

            # most commonly used resolution
            res_counts = Counter(tex_resolutions.values())
            most_common_resolution, _count = res_counts.most_common()[0]

            # mismatches
            failed_textures = [
                cls.FailureInfo(
                    filename=os.path.basename(filepath),
                    expected=most_common_resolution,
                    found=res,
                )
                for filepath, res in tex_resolutions.items()
                if res != most_common_resolution
            ]

            if failed_textures:
                material = bpy.data.materials[material_name]
                failed_materials[material] = sorted(failed_textures, key=lambda t: t.filename)

        return failed_materials


@cgtcheck.runners.CheckRunner.register
class CheckSingleUVChannel(Check, Properties):
    """
    Check mesh objects for improper number of UV channels (multiple or none).
    """

    key = 'singleUVChannel'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[Object, int] = {}

    def run(self) -> Dict[Object, int]:
        """
        Return a list of objects which mesh don't contain a single UV layer.
        Collect amount of UV layers per mesh for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            if obj.data and obj.data.uv_layers is not None:
                uv_amount = len(obj.data.uv_layers)
                self.properties.append({'id': i, 'uv_amount': uv_amount})
                if uv_amount != 1:
                    self.failures[obj] = len(obj.data.uv_layers)

        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(obj.name) for obj in self.failures]

    def format_failure(self, failed_mesh: Object) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_mesh.name,
            'expected': 0,
            'found': self.failures[failed_mesh],
        }


@cgtcheck.runners.CheckRunner.register
class CheckTopLevelZeroPosition(Check, Properties):
    """
    Check top-level mesh objects for pivot point location not at world origin (0, 0, 0).
    """

    key = 'topLevelZeroPosition'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[Object, Tuple[float, float, float]]]:
        """
        Return a list of objects and pivots, where pivot point is not located at world origin.
        Return pivot point location for each object to the property report.
        """
        deviation = self.params.get('parameters', {}).get("positionDeviation", 0.001)

        for i, obj in enumerate(self.collector.objects):
            self.properties.append(
                {'id': i,
                 'pivot_position': (obj.location.x,
                                    obj.location.y,
                                    obj.location.z)
                 }
            )
            if obj.parent is None and (abs(obj.location.x) > deviation
                                       or abs(obj.location.y) > deviation
                                       or abs(obj.location.z) > deviation):
                self.failures.append((obj, tuple(obj.location)))

        return self.failures

    def list_failures(self) -> List[object]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(obj.name) for obj, _pivot in self.failures]

    def format_failure(
        self,
        failure: Tuple[Object, Tuple[float, float, float]]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj, pivot = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj.name,
            'expected': (0, 0, 0),
            'found': pivot,
        }


@cgtcheck.runners.CheckRunner.register
class CheckCenteredGeometryBoundingBox(Check, Properties):
    """
    Check if the bounding box of the scene geometry is correctly centered
    """

    key = 'centeredGeometryBoundingBox'
    version = (0, 1, 3)
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.properties: Dict[str, Tuple[int, int, int]] = {}

    def run(self) -> List[str]:
        """
        Return a list containing empty dict when combined bounding box of all mesh objects
        has the bottom center point not within the 'positionDeviation' threshold value.
        Return empty list otherwise.
        Return the bottom midpoint position of the connected bounding box of all objects
        to the property report.
        """
        unit_multiplier = bpy.context.scene.unit_settings.scale_length
        deviation = self.params.get('parameters', {}).get("positionDeviation", (0.1, 0.1, 0.1))
        deviation = [axis / unit_multiplier for axis in deviation]

        model_b_box = dimensions.get_bounding_box(self.collector.objects)
        bbox_bottom_center = [
            model_b_box[0][0] + (model_b_box[1][0] - model_b_box[0][0]) / 2,
            model_b_box[0][1] + (model_b_box[1][1] - model_b_box[0][1]) / 2,
            model_b_box[0][2]
        ]

        is_bounding_box_centered = (
            abs(bbox_bottom_center[0]) <= deviation[0]
            and abs(bbox_bottom_center[1]) <= deviation[1]
            and abs(bbox_bottom_center[2]) <= deviation[2]
        )

        self.properties.update(
            {
                'bottom_center_position': (
                    (bbox_bottom_center[0]),
                    (bbox_bottom_center[1]),
                    (bbox_bottom_center[2])
                )
            }
        )

        if not is_bounding_box_centered:
            self.failures = ['Model']

        return self.failures

    def list_failures(self) -> List:
        """
        Returns list of found issues for this check
        """
        return []

    def get_failures(self) -> List:
        """
        Returns empty list, since this check does not have failure items
        """
        return []


@cgtcheck.runners.CheckRunner.register
class CheckCenteredChildPivots(Check, Properties):
    """
    Check that pivots of parent mesh objects are centered in child objects.
    """

    key = 'centeredChildPivots'
    version = (0, 1, 1)
    failures: List[Tuple[Object, Vector]] = []
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[Object, Vector]]:
        """
        Return a list of child objects which have pivot position deviated from
        bounding box center by more than `positionDeviation` threshold, for any coordinate.
        Return pivot point location and bounding box center for each object to the property report.
        """
        deviation = self.params.get('parameters', {}).get('positionDeviation', 0.001)

        for i, obj in enumerate(self.collector.objects):
            bbmin, bbmax = dimensions.object_bounds(obj)
            bb_center = (Vector(bbmin) + Vector(bbmax)) * 0.5
            self.properties.append(
                {'id': i,
                 'pivot_position': (obj.location.x,
                                    obj.location.y,
                                    obj.location.z),
                 'bb_center': (bb_center.x,
                               bb_center.y,
                               bb_center.z)
                 }
            )
            if obj.parent is not None and (any(abs(offset) > deviation
                                               for offset in (obj.location - bb_center))):
                self.failures.append((obj, bb_center))

        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(obj.name) for obj, bb_center in self.failures]

    def format_failure(
        self,
        failure: Tuple[Object, Vector]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj, bb_center = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj.name,
            'expected': tuple(bb_center),
            'found': tuple(obj.location),
        }


@cgtcheck.runners.CheckRunner.register
class CheckRequiredTextures(Check, Properties):
    """
    Check if all defined maps in required_textures are present.
    """

    key = 'missingRequiredTextures'
    version = (0, 1, 3)

    def run(self) -> List[str]:
        """
        Return a list of maps not delivered which are defined in required_textures.
        """
        tex_paths = self.collector.mat_texture_path
        tex_spec = self.collector.tex_spec
        input_file = self.collector.input_file or ''
        tex_patterns = TexPatterns(tex_spec) if tex_spec else TexPatterns()

        for matname, textures in tex_paths.items():
            materials_name_id = {mat.name: self.collector.materials.index(mat) for
                                 mat in self.collector.materials}
            # reset substitutions for generate_filename
            tex_patterns.reset_substitutions()
            try:
                tex_patterns.substitute(infile=input_file, matname=matname)
            except ParseError as exc:
                logger.warning('Incorrect material name: {}, expected: {}'.format(
                    exc.args[2], more_readable_re(exc.args[3])
                ))
                continue

            for required_tex in tex_patterns.required_textures:
                generated_filename = str(tex_patterns.generate_filename(
                    required_tex,
                    ext="",
                    fallback=required_tex,
                    from_output_files=False,
                    remove_escape_symbols=False
                ))

                generated_filename = more_readable_re(generated_filename)
                generated_filename = self._remove_backslashes(generated_filename)
                texture_delivered = (
                    required_tex in textures.keys() and os.path.exists(textures[required_tex])
                )
                self.properties.append(
                    {
                        'material': materials_name_id[matname],
                        'name': generated_filename,
                        'delivered': texture_delivered
                    }
                )
                if not texture_delivered:
                    if generated_filename not in self.failures:
                        self.failures.append(generated_filename)

        self.failures.sort()
        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }

    @classmethod
    def _remove_backslashes(cls, input):
        """
        Removes backslash characters
        """
        return re.sub(r'\\(.)', r'\1', input)

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckMultiMaterial(Check, Properties):
    """
    Check if more than one material assigned to mesh.
    Collect materials ID per mesh for properties report.
    """

    key = 'multiMaterial'
    version = (0, 1, 1)
    expected_value = 1
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        for i, obj in enumerate(self.collector.objects):
            materials_id = [self.collector.materials.index(mat) for
                            mat in obj.data.materials if mat is not None]
            self.properties.append({'id': i, 'materials': materials_id})
            if len(obj.data.materials) > self.expected_value:
                self.failures.append(obj)
        return self.failures

    def format_failure(self, failed_obj: Object) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': self.expected_value,
            'found': len(failed_obj.data.materials),
        }


@cgtcheck.runners.CheckRunner.register
class CheckTextureResolutionsNotPowerOf2(Check, Properties):
    """
    Check if texture resolution is a power of 2.
    """

    key = 'textureResolutionNotPowerOf2'
    version = (0, 1, 0)

    def run(self) -> List[Tuple[str, Tuple[int, int], Tuple[int, int]]]:
        """
        Return a list of textures with a not-power-of-2 resolution.
        Collect resolution per texture for properties report.
        """
        tex_paths = self.collector.mat_texture_path
        tex_in_spec = {tex_path: str for mat in tex_paths.values() for tex_path in mat.values()}

        for tex in tex_in_spec:
            if not os.path.exists(tex):
                logger.warning('Not found on disk, skipping: %s', tex)
                continue
            with Image.open(tex) as img:
                w, h = img.size
                self.properties.append(
                    {
                        'name': os.path.basename(tex),
                        'resolution': [w, h]
                    }
                )
                if not all(self._is_power_of_2(d) for d in (w, h)):
                    found_size = int(w), int(h)
                    expected_size = (self._get_closest_lower_power_of_2(w),
                                     self._get_closest_lower_power_of_2(h))
                    self.failures.append((str(os.path.basename(tex)), found_size, expected_size))

        return self.failures

    def format_failure(
        self,
        failure: Tuple[str, Tuple[int, int], Tuple[int, int]]
    ) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'item': filename,
            'found': found,
            'expected': expected,
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    @classmethod
    def _is_power_of_2(cls, value: int) -> bool:
        return log(value, 2).is_integer()

    @classmethod
    def _get_closest_lower_power_of_2(cls, value: int) -> int:
        if value < 2:
            return 2
        return 2 ** (floor(log(value, 2)))


@cgtcheck.runners.CheckRunner.register
class CheckNoTransparentMeshes(Check, Properties):
    """
    Check that there are no transparent meshes present.
    """

    key = 'noTransparentMeshes'
    version = (0, 1, 2)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[str, Tuple[str]]]:
        """
        Return Color and Opacity maps name with resolution if are not the same resolution.
        """
        transparent_objects_materials = self._find_objects_with_transparent_materials()

        if transparent_objects_materials:
            for obj, mats in transparent_objects_materials.items():
                self.failures.append((obj.name, tuple(str(m.name) for m in mats)))

        return self.failures

    def format_failure(self, failure: Tuple[str, Tuple[str]]) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj_name, materials = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj_name,
            'materials': ', '.join('"%s"' % m for m in materials),
        }

    def _find_objects_with_transparent_materials(self) -> Dict[Object, Set[Material]]:
        """
        Returns a dictionary containing objects and their respective transparent materials.
        Collect information if object is transparent and blending method for each object
        and material id for the properties report.

        Example:
            >>> self._find_objects_with_transparent_materials()
            {bpy.data.objects['IceCube']: {bpy.data.materials['Ice_mat']},
             bpy.data.objects['Water']: {bpy.data.materials['Liquid_mat']}}
        """
        objects_transparent_mats = {}

        for i, obj in enumerate(self.collector.objects):
            materials_name_id = {
                mat.name: self.collector.materials.index(mat)
                for mat in obj.data.materials if mat is not None
            }
            transparent_materials = set()
            if obj.data.materials:
                for material_slot in obj.material_slots:
                    material = material_slot.material
                    if material.blend_method != 'OPAQUE':
                        transparent_materials.add(material)
                        continue
                    if material.node_tree is None:
                        continue
                    for node in material.node_tree.nodes:
                        alpha_not_one = False
                        if 'Alpha' in node.inputs:
                            alpha_input = node.inputs['Alpha']
                            alpha_not_one = alpha_input.default_value != 1 or bool(alpha_input.links)  # noqa E501
                        is_transparent = alpha_not_one or ('GLASS' in node.type)
                        if is_transparent:
                            transparent_materials.add(material)

            self.properties.append(
                {
                    'id': i,
                    'materials': list(materials_name_id.values()),
                    'transparent': bool(transparent_materials),
                }
            )
            if transparent_materials and not obj.get('is_shadow_plane'):
                objects_transparent_mats[obj] = transparent_materials

        return objects_transparent_mats


@cgtcheck.runners.CheckRunner.register
class CheckNoUvTiling(Check, Properties):
    """
    Check mesh objects for improper UV coordinates (outside the 0 to 1 range).
    """

    key = 'noUvTiling'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[str, List[str]]]:
        """
        Return list of objects & their UV layers the UV coords of which are outside the 0-1 range.
        Collect information if UV coordinates are (outside the 0-1 range)
        per mesh for properties report.
        """
        mesh_objects_with_uv_tiling = []
        for i, obj in enumerate(self.collector.objects):
            uv_layer_names_uvs_outside_0_to_1 = []
            self.properties.append({'id': i, 'uv_inside': [], 'uv_outside': []})
            uv_layer_names = [u.name for u in obj.data.uv_layers]
            for uv_layer_name in uv_layer_names:
                uv_layer = obj.data.uv_layers[uv_layer_name]
                uvs_outside_0_to_1 = False
                for uv_coords in uv_layer.data:
                    u, v = uv_coords.uv
                    if (u < 0) or (v < 0) or (u > 1) or (v > 1):
                        uvs_outside_0_to_1 = True
                        break
                if uvs_outside_0_to_1:
                    uv_layer_names_uvs_outside_0_to_1.append(uv_layer_name)
                    self.properties[i].setdefault('uv_outside', []).append(uv_layer_name)
                else:
                    self.properties[i].setdefault('uv_inside', []).append(uv_layer_name)
            if uv_layer_names_uvs_outside_0_to_1:
                mesh_objects_with_uv_tiling.append(
                    (obj.name, uv_layer_names_uvs_outside_0_to_1)
                )

        self.failures = mesh_objects_with_uv_tiling
        return self.failures

    def format_failure(
        self,
        failure: Tuple[str, List[str]]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj_name, uv_layer_names = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj_name,
            'uv_layers': ', '.join('"%s"' % uv_layer for uv_layer in uv_layer_names),
        }


@cgtcheck.runners.CheckRunner.register
class CheckObjectByMaterialTypeCount(Check, Properties):
    """
    Checks scene for objects with assigned material types (BLEND, OPAQUE) amount
    """

    key = 'objectByMaterialTypeCount'
    version = (0, 1, 2)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[object, int, str, int]]:
        """
        Checks scene objects active material parameter "blend_method" value
        Returns list of found issues for this check
        """
        compareop = {
            '=': operator.eq,
            '<': operator.lt,
            '>': operator.gt,
            '<=': operator.le,
            '>=': operator.ge
        }
        object_types = {
            'OPAQUE': set(),
            'BLEND': set(),
            'CLIP': set()
        }
        all_params = {
            'opaque_type_objects': 'OPAQUE',
            'blend_type_objects': 'BLEND',
            'clip_type_objects': 'CLIP'
        }
        type_priority = ['CLIP', 'BLEND', 'OPAQUE']  # Types priority (multimaterial-case)

        obj_type_to_blend_mode = self.params.get('parameters', {})

        for i, obj in enumerate(self.collector.objects):
            obj_material_types = []
            for material_slot in obj.material_slots.values():
                mat_type = material_slot.material.blend_method
                obj_material_types.append(mat_type)

            self.properties.append({'id': i, 'type': obj_material_types})
            if obj.get('is_shadow_plane'):
                continue

            for priority in type_priority:
                # defines object type based on type priority order
                if priority in obj_material_types:
                    object_types[priority].add(i)
                    break

        for type_check, params in obj_type_to_blend_mode.items():
            object_type = all_params[type_check]
            comparator = params['comparator']
            expected = params['count']
            found = len(object_types[object_type])

            if not compareop[comparator](found, expected):
                failure = (object_type, found, comparator, expected)
                self.failures.append(failure)

        return self.failures

    def format_failure(
        self,
        failure: Tuple[str, str, int]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        (object_type, found, comparator, expected) = failure
        return {
            'message': self.metadata.item_msg,
            'object_type': object_type,
            'comparator': comparator,
            'found': found,
            'expected': expected,
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        all_params = {
            'opaque_type_objects': 'OPAQUE',
            'blend_type_objects': 'BLEND',
            'clip_type_objects': 'CLIP'
        }
        obj_type_to_blend_mode = self.params.get('parameters', {})
        expected_values = []
        for type_check, params in obj_type_to_blend_mode.items():
            object_type = all_params[type_check]
            comparator = params['comparator']
            expected = params['count']
            expected_values.append(str(f'{object_type} {comparator} {expected}'))
        return self.metadata.check_description.format(', '.join(expected_values))


TransformsResetStatus = namedtuple('TransformsFailure', 'translated, rotated, scaled')


@cgtcheck.runners.CheckRunner.register
class CheckResetTransforms(Check, Properties):
    """
    Check objects for not reseted transforms
    """

    key = 'dccResetTransforms'
    version = (0, 2, 1)
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs):
        super(CheckResetTransforms, self).__init__(*args, **kwargs)

    def run(self) -> List[tuple[Mesh, TransformsResetStatus]]:
        """
        Returns failed items.
        """
        parameters = self.params.get('parameters', {})
        check_position = parameters.get('position', False)
        check_rotation = parameters.get('rotation', True)
        check_scale = parameters.get('scale', True)
        float_tolerance = parameters.get('floatTolerance', 0.001)
        allow_instances = parameters.get('allowInstances', False)
        x_axis_rotation = parameters.get('xAxisRotation', 0.0)
        y_axis_rotation = parameters.get('yAxisRotation', 0.0)
        z_axis_rotation = parameters.get('zAxisRotation', 0.0)

        expected_euler = Euler(
            (
                radians(x_axis_rotation),
                radians(y_axis_rotation),
                radians(z_axis_rotation)
            ),
            'XYZ')
        expected_values = (
            (check_position, 'location', Vector((0.0, 0.0, 0.0)), 'position'),
            (check_rotation, 'rotation_euler', expected_euler, 'rotation'),
            (check_scale, 'scale', Vector((1.0, 1.0, 1.0)), 'scale'),
        )
        fbx_compatible_objects = self.collect_objects(allow_instances)
        for index, obj in enumerate(fbx_compatible_objects):
            self.properties.append({'id': index})
            for _, attr, _, unified_attr_name in expected_values:
                if attr == 'rotation_euler':
                    pass
                    self.properties[index].update(
                        {unified_attr_name: [round(degrees(i), 3) for i in getattr(obj, attr)]}
                    )
                else:
                    pass
                    self.properties[index].update(
                        {unified_attr_name: [round(i, 3) for i in getattr(obj, attr)]}
                    )

            prs_transformed_states = (
                None if not is_enabled else not self.near_equal_vect(
                    getattr(obj, attr), value, float_tolerance,
                )
                for is_enabled, attr, value, _ in expected_values
            )
            transforms_status = TransformsResetStatus(*prs_transformed_states)
            if any(transforms_status):
                self.failures.append((obj, transforms_status))
        return self.failures

    def collect_objects(self, allow_instances=False) -> List[Mesh]:
        """
        Returns list of objects for check
        """
        if allow_instances:
            return [
                o for o in self.collector.fbx_exportable_objects
                if o.type == 'EMPTY' or o.data.users == 1
            ]

        return self.collector.fbx_exportable_objects

    @staticmethod
    def near_equal_vect(a: tuple[float], b: tuple[float], float_tolerance=0.001) -> bool:
        """
        Return True if vector `a` equals vector `b` within the specified tolerance.
        Vector in this context is any length iterable of floats. Number of elements must match.
        """
        return all(abs(va - vb) <= float_tolerance for va, vb in zip(a, b))

    def list_failures(self) -> list[str]:
        """
        Returns list of found issues for this check.
        """
        formatted_failures = (self.format_failure(f) for f in self.failures)
        return (f['message'].format(**f) for f in formatted_failures)

    def format_failure(
        self,
        failure:
        tuple[object, TransformsResetStatus]
    ) -> dict[str, str | bool]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj, status = failure
        return {
            u'message': self.metadata.item_msg,
            u'item': obj.name,
            u'expected': False,
            u'found': True,
            u'translated': status.translated,
            u'rotated': status.rotated,
            u'scaled': status.scaled,
            u'transformedKindsText': u', '.join(
                tmtype for tmtype, is_failed in zip(status._fields, status)
                if is_failed
            ),
        }

    def format_details(self) -> dict[str, str | bool] | None:
        """
        Format a details report to be sent to Wildcat.
        Returns None if the check is not enabled to be reported as details.
        """
        if self.report_type != 'details':
            return None
        return {
            self.key: {
                'failed': not self.passed,
                'text': self.fail_message(),
                'title': 'Node transforms reset',
                'type': 'warning',
            }
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        parameters = self.params.get('parameters', {})
        check_position = parameters.get('position', False)
        check_rotation = parameters.get('rotation', True)
        check_scale = parameters.get('scale', True)
        x_axis_rotation = parameters.get('xAxisRotation', 0.0)
        y_axis_rotation = parameters.get('yAxisRotation', 0.0)
        z_axis_rotation = parameters.get('zAxisRotation', 0.0)

        expected_rotation = str(f'{x_axis_rotation}, {y_axis_rotation}, {z_axis_rotation}')
        expected_transforms = (
            (check_position, 'position', '0.0, 0.0, 0.0'),
            (check_rotation, 'rotation', expected_rotation),
            (check_scale, 'scale', '1, 1, 1'),
        )

        expected_values = [
            None if not is_enabled else str(f'{transform}: {value}')
            for is_enabled, transform, value in expected_transforms
        ]
        expected_values = filter(None, expected_values)
        return self.metadata.check_description.format(', '.join(expected_values))


@cgtcheck.runners.CheckRunner.register
class CheckFlippedUv(Check, Properties):
    """
    Check mesh objects for flipped (mirrored) UVs.
    """

    key = 'flippedUv'
    version = (0, 1, 2)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[str, List[str]]]:
        """
        Return list of objects & their UV layers if any UV face is flipped.
        Collect information if UV coordinates are (flipped/mirrored) per mesh for properties report.
        """
        mesh_objects_with_flipped_uv = []
        for i, obj in enumerate(self.collector.objects):
            uv_layers_with_flipped_faces = []
            self.properties.append(
                {
                    'id': i,
                    'uv_with_flipped_faces': [],
                    'uv_without_flipped_faces': []
                }
            )

            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='FIXED')
            for uv_layer in bm.loops.layers.uv.items():
                uv_layer_name = uv_layer[0]
                flipped_uv_face = False
                for face in bm.faces:
                    sum_edges = 0
                    for j in range(3):
                        uv_a = face.loops[j][uv_layer[1]].uv
                        uv_b = face.loops[(j + 1) % 3][uv_layer[1]].uv
                        sum_edges += (uv_b.x - uv_a.x) * (uv_b.y + uv_a.y)

                    if sum_edges > 0:
                        flipped_uv_face = True
                        break

                if flipped_uv_face:
                    uv_layers_with_flipped_faces.append(uv_layer_name)
                    self.properties[i].setdefault('uv_with_flipped_faces', []).append(
                        uv_layer_name
                    )
                else:
                    self.properties[i].setdefault('uv_without_flipped_faces', []).append(
                        uv_layer_name
                    )
            bm.free()
            if uv_layers_with_flipped_faces:
                mesh_objects_with_flipped_uv.append((obj.name, uv_layers_with_flipped_faces))

        self.failures = mesh_objects_with_flipped_uv
        return self.failures

    def format_failure(
        self,
        failure: Tuple[str, List[str]]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj_name, uv_layers_names = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj_name,
            'uv_layers': ', '.join('"%s"' % uv_layer for uv_layer in uv_layers_names),
        }


class CheckOverlappedUvBase(Check, Properties):

    format_properties = Properties._basic_format_properties

    def _pack_uv_island(self) -> None:
        """
        Pack uv islands for active UV layers. It's meant to be overwritten.
        """
        pass

    @contextmanager
    def _prepare_object_to_check(self, obj: bpy.types.Object):
        """
        Yields object to check
        Args:
            obj: object for which we want to check UV's
        """
        raise NotImplementedError('DCC-specific packager class should override this method')

    def _has_zero_area_uv_island(self, obj: bpy.types.Object, uv_index: int) -> bool:
        """
        Checks if any UV island for given object and uv_index is zero area

        Args:
            obj: object for which we want to check UV's
            uv_index: uv for which we want to check UV's
        Returns:
            True if uv area is considered as zero area, False otherwise

        """
        for uv_island in mesh_utils.mesh_linked_uv_islands(obj.data):
            uv_area = uv.uv_faces_area(uv_island, obj.data, uv_index)
            if uv_area < 1e-10:
                return True

        return False

    def run(self) -> List[Tuple[List[str], List[str], str]]:
        """
        Return list of objects & their UV layers if any UV face overlapped.
        Collect information if UV contain overlapped parts per mesh for properties report.
        """
        initial_active = bpy.context.view_layer.objects.active
        initial_selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        failed_obj = set()
        for i, obj in enumerate(self.collector.objects):
            if not obj.data.polygons:  # skip objects without geometry
                continue
            if obj.hide_viewport:
                logger.info('%s check skipped viewport-hidden object: %s', self.key, obj.name)
                continue
            zero_area_uv = []
            overlapped_uv: List[str] = []
            no_overlapped_uv: List[str] = []
            self.properties.append({
                'id': i,
                'overlapped_uv': overlapped_uv,
                'no_overlapped_uv': no_overlapped_uv,
            })
            bpy.context.view_layer.objects.active = obj

            #  skipping zero area uv
            for uv_index, uv_layer in enumerate(obj.data.uv_layers):
                obj.data.uv_layers.active = uv_layer
                if self._has_zero_area_uv_island(obj, uv_index):
                    zero_area_uv.append(uv_index)

            with self._prepare_object_to_check(obj) as obj_to_check:
                bpy.ops.object.mode_set(mode='EDIT')
                for uv_index, uv_layer in enumerate(obj_to_check.data.uv_layers):
                    if uv_index not in zero_area_uv:
                        obj_to_check.data.uv_layers.active = uv_layer
                        self._pack_uv_island()
                        bpy.ops.uv.select_overlap()
                bpy.ops.object.mode_set(mode='OBJECT')

                uv_layer_names = [u.name for u in obj_to_check.data.uv_layers]
                for uv_layer_name in uv_layer_names:
                    uv_layer = obj_to_check.data.uv_layers[uv_layer_name]
                    is_overlapped_uv = False
                    obj_to_check.data.uv_layers.active = uv_layer
                    for uv_loop in uv_layer.data:
                        if uv_loop.select:
                            is_overlapped_uv = True
                            break
                    if is_overlapped_uv or zero_area_uv:
                        failed_obj.add(obj)
                        overlapped_uv.append(uv_layer_name)
                    else:
                        no_overlapped_uv.append(uv_layer_name)

            if overlapped_uv:
                self.failures.append(
                    (
                        [o.name for o in failed_obj],
                        overlapped_uv,
                        'in UV layer(s)):'
                    )
                )
        bpy.ops.object.select_all(action='DESELECT')
        for obj in initial_selection:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = initial_active

        return self.failures

    def format_failure(
        self,
        failure: Tuple[List[str], List[str], str]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        failed_obj_names, uv_layers_names, msg_type = failure
        return {
            'message': self.metadata.item_msg,
            'item': ', '.join('"%s"' % obj for obj in failed_obj_names),
            'msg_type': msg_type,
            'uv_layers': ', '.join('"%s"' % uv_layer for uv_layer in uv_layers_names),
        }


@cgtcheck.runners.CheckRunner.register
class CheckOverlappedPerUvObject(CheckOverlappedUvBase):
    """
    Check mesh objects for overlapped UVs per object.
    """

    key = 'overlappedUvPerObject'
    version = (1, 0, 1)

    @contextmanager
    def _prepare_object_to_check(self, obj: bpy.types.Object):

        yield obj


@cgtcheck.runners.CheckRunner.register
class CheckOverlappedUvPerUVIsland(CheckOverlappedUvBase):
    """
    Check if UV island in mesh has overlapped UVs
    """

    key = 'overlappedUvPerUVIsland'
    version = (0, 1, 0)

    def _pack_uv_island(self) -> None:
        """
        Pack uv islands for active UV layers
        """
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands()
        bpy.ops.uv.select_all(action='DESELECT')

    @contextmanager
    def _prepare_object_to_check(self, obj: bpy.types.Object):

        temp_obj = obj.copy()
        temp_obj.data = temp_obj.data.copy()
        bpy.context.collection.objects.link(temp_obj)
        temp_obj.select_set(True)
        try:
            yield temp_obj
        finally:
            bpy.ops.object.delete(use_global=False, confirm=False)


@cgtcheck.runners.CheckRunner.register
class CheckOverlappedUvPerModel(Check, Properties):
    """
    Check mesh objects for overlapped UVs between them all.
    """

    key = 'overlappedUvPerModel'
    version = (0, 1, 2)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.properties: Dict[str, Dict] = {}

    def run(self) -> List[Tuple[List[str], List[str]], str]:
        """
        Return list of objects or materials & their UV layers if any UV face overlapped.
        Collect information if UV contain overlapped parts per mesh for properties report.
        """
        overlapped_uv = []
        initial_active = bpy.context.view_layer.objects.active
        initial_selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        failed_obj = set()
        uv_layers_with_overlapped_faces = []
        initial_active_layers = {}
        objects_with_uvs: Dict[int, bpy.types.Object] = {}
        objects_without_uvs: Dict[int, bpy.types.Object] = {}
        for i, obj in enumerate(self.collector.objects):
            if not obj.data.polygons:  # skip objects without geometry
                continue
            (objects_with_uvs if obj.data.uv_layers else objects_without_uvs)[i] = obj

        if objects_with_uvs:
            bpy.context.view_layer.objects.active = next(iter(objects_with_uvs.values()))

            for obj in objects_with_uvs.values():
                initial_active_layers[obj] = obj.data.uv_layers.active.name
                obj.data.uv_layers.active = obj.data.uv_layers[0]

            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            for obj in objects_with_uvs.values():
                obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.select_overlap()
            bpy.ops.object.mode_set(mode='OBJECT')

            for i, obj in objects_with_uvs.items():
                self.properties[i] = obj_properties = {'overlapped_uv': [], 'no_overlapped_uv': []}
                is_overlapped_uv = False
                for uv_layer in obj.data.uv_layers[0].data:
                    uv_layer_name = obj.data.uv_layers[0].name
                    if uv_layer.select:
                        is_overlapped_uv = True
                        break
                if is_overlapped_uv:
                    uv_layers_with_overlapped_faces.append(uv_layer_name)
                    failed_obj.add(obj)
                    obj_properties['overlapped_uv'].append(obj.name)
                else:
                    obj_properties['no_overlapped_uv'].append(obj.name)

                obj.data.uv_layers.active = obj.data.uv_layers[initial_active_layers[obj]]

            if uv_layers_with_overlapped_faces:
                overlapped_uv.append(
                    (sorted([o.name for o in failed_obj]), [], 'among themselves')
                )

        bpy.ops.object.select_all(action='DESELECT')
        for obj in initial_selection:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = initial_active

        self.failures = overlapped_uv
        return self.failures

    def format_failure(
        self,
        failure: Tuple[List[str], List[str], str]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        failed_obj_names, uv_layers_names, msg_type = failure
        return {
            'message': self.metadata.item_msg,
            'item': ', '.join('"%s"' % obj for obj in failed_obj_names),
            'msg_type': msg_type,
            'uv_layers': ', '.join('"%s"' % uv_layer for uv_layer in uv_layers_names),
        }

    def _flattened_properties(self) -> Generator[Dict]:
        """
        Generator into properties in the format {'id':, <prop0>:, <prop1>:, ...}
        """
        for obj_i, props in self.properties.items():
            flat = {'id': obj_i}
            flat.update(props)
            yield flat

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'objects': list(self._flattened_properties())
        }


@cgtcheck.runners.CheckRunner.register
class CheckOverlappedUvPerMaterial(Check, Properties):
    """
    Check mesh objects of the same material for overlapped UVs.
    """

    key = 'overlappedUvPerMaterial'
    version = (1, 0, 0)

    def run(self) -> List[Tuple[List[str], List[str], str]]:
        """
        Return list of objects or materials & their UV layers if any UV face overlapped.
        Collect information if UV contain overlapped parts per mesh for properties report.
        """
        if not self.collector.objects:
            return []

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        initial_active = bpy.context.view_layer.objects.active
        initial_selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')

        if bpy.context.view_layer.objects.active is None:
            bpy.context.view_layer.objects.active = self.collector.objects[0]
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        uv_objects_to_ids: Dict[bpy.types.Object, int] = {
            obj: i for i, obj in enumerate(self.collector.objects)
            if hasattr(obj.data, 'uv_layers') and obj.data.uv_layers
        }
        for mat_i, material in enumerate(self.collector.materials):
            for obj in uv_objects_to_ids:
                mesh: bpy.types.Mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)
                mat_index = bcommon.material_index(mesh, material)
                if mat_index >= 0:
                    for face in bm.faces:
                        if face.material_index == mat_index:
                            face.select = True
                        else:
                            face.select = False
                    obj.select_set(True)
                else:
                    for face in bm.faces:
                        face.select = False
                    obj.select_set(False)
                bm.to_mesh(mesh)
                bm.clear()
                bm.free()
                mesh.update()

            if not bpy.context.selected_objects:
                logger.info('%s check skipping unused material: %s', self.key, material.name)
                continue

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.select_overlap()
            bpy.ops.object.mode_set(mode='OBJECT')
            obj_to_overlapped_layers: Dict[bpy.types.Object, List[str]] = {}
            for obj in uv_objects_to_ids:
                overlapped_uvs = []
                for uv_layer in obj.data.uv_layers:
                    is_overlapped_uv = False
                    obj.data.uv_layers.active = uv_layer
                    for uv_loop in uv_layer.data:
                        if uv_loop.select:
                            is_overlapped_uv = True
                            break
                    if is_overlapped_uv:
                        overlapped_uvs.append(uv_layer.name)
                if overlapped_uvs:
                    obj_to_overlapped_layers[obj] = overlapped_uvs

            if obj_to_overlapped_layers:
                failed_layers = set()
                for layer_names in obj_to_overlapped_layers.values():
                    failed_layers.update(layer_names)
                self.failures.append(
                    (
                        [obj.name for obj in obj_to_overlapped_layers],
                        sorted(failed_layers),
                        'in UV layer(s)):'
                    )
                )

            self.properties.append({
                'material': mat_i,
                'overlaps': [
                    {
                        'object': uv_objects_to_ids[obj],
                        'uv_layers': layers,
                    }
                    for obj, layers in obj_to_overlapped_layers.items()
                ]
            })

        bpy.ops.object.select_all(action='DESELECT')
        for obj in initial_selection:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = initial_active

        return self.failures

    def format_failure(
        self,
        failure: Tuple[List[str], List[str], str]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        failed_obj_names, uv_layers_names, msg_type = failure
        return {
            'message': self.metadata.item_msg,
            'item': ', '.join('"%s"' % obj for obj in sorted(failed_obj_names)),
            'msg_type': msg_type,
            'uv_layers': ', '.join('"%s"' % uv_layer for uv_layer in uv_layers_names),
        }

    def format_properties(self) -> Dict[str, Dict]:
        """
        Format a property report.
        """
        return {
            'materials': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckConnectedTextures(Check, Properties):
    """
    Check materials for connected textures by material slot
    """

    key = 'connectedTextures'
    version = (0, 1, 0)

    slot_map = {
        'opacity': 'Alpha',
        'anisotropic': 'Anisotropic',
        'anisotropic_angle': 'Anisotropic Rotation',
        'base_color': 'Base Color',
        'emissive': 'Emission',
        'ior': 'IOR',
        'metallic': 'Metallic',
        'normal': 'Normal',
        'roughness': 'Roughness',
        'sheen': 'Sheen',
        'specular': 'Specular',
        'subsurface': 'Subsurface',
    }

    @dataclass
    class FailureInfo:
        missing: List[str]
        forbidden: List[str]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[bpy.types.Material, CheckConnectedTextures.FailureInfo] = {}

    def run(self) -> Dict[bpy.types.Material, FailureInfo]:
        """
        Returns any materials which had textures connected to forbidden slots,
        or textures were not connected where they were required to be.
        """
        check_params = self.params.get('parameters', {})
        metadata_params = self.metadata.params.get('parameters', {})
        required_slots = set(check_params.get('required', metadata_params['required']))
        forbidden_slots = set(check_params.get('forbidden', metadata_params['forbidden']))

        materials: List[bpy.types.Material] = self.collector.materials
        for mat_i, mat in enumerate(materials):
            if not mat.use_nodes:
                logger.warning(
                    f'Material {mat.name} not using nodes. '
                    'Will not validate connectedTextures for it.'
                )
                continue
            bsdf: bpy.types.ShaderNodeBsdfPrincipled = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf is None:
                logger.warning(
                    f'No Princiled BSDF node found for material {mat.name}. '
                    'Will not validate connectedTextures for it.'
                )
                continue

            slots_with_images = {
                slot_key for slot_key, slot_dcc_key in self.slot_map.items()
                if next(self._image_textures_at_input(bsdf.inputs[slot_dcc_key]), None)
            }
            self.properties.append({'id': mat_i, 'slots': list(sorted(slots_with_images))})

            missing = required_slots - slots_with_images
            forbidden = slots_with_images & forbidden_slots
            if missing or forbidden:
                self.failures[mat] = self.FailureInfo(
                    missing=list(sorted(missing)),
                    forbidden=list(sorted(forbidden)),
                )

        return self.failures

    @classmethod
    def _is_acceptable_image_node(
        cls,
        node: bpy.types.ImageTexture,
        allow_embedded=True,
        allow_missing=True
    ) -> bool:
        """
        Returns true if supplied node meets the requirements for an image node.
        """
        if node.type != 'TEX_IMAGE':
            return False

        image = node.image
        if not image:
            return False

        if image.source == 'FILE':
            return allow_missing or os.path.isfile(image.filepath)
        elif allow_embedded and image.source == 'GENERATED':
            return True

        return False

    @classmethod
    def _image_textures_at_input(
        cls,
        input: bpy.types.NodeSocket,
        allow_embedded=True,
        allow_missing=True,
    ) -> Generator[bpy.types.ImageTexture]:
        """
        Iterates over any image textures connected to an input, at any depth.

        Args:
            input: a node input to scan for image textures
            allow_embedded: include image textures which aren't file-based
            allow_missing: allow associated image files to be missing
        """
        for link in input.links:
            node: bpy.types.Node = link.from_node
            if cls._is_acceptable_image_node(
                node,
                allow_embedded=allow_embedded,
                allow_missing=allow_missing,
            ):
                yield node
            else:
                for input in node.inputs:
                    yield from cls._image_textures_at_input(
                        input,
                        allow_embedded=allow_embedded,
                        allow_missing=allow_missing,
                    )

    def get_failures(self) -> Generator[Tuple[str, bpy.types.Material, FailureInfo]]:
        """
        Returns generator over failures, with failure type prepended. Every failure
        which has both forbidden and missing textures will be iterated as two separate ones.
        """
        for failed_mat, fail_info in self.failures.items():
            if fail_info.missing:
                yield ('missing', failed_mat, fail_info)
            if fail_info.forbidden:
                yield ('forbidden', failed_mat, fail_info)

    def format_failure(
        self,
        failure: Tuple[bpy.types.Material, FailureInfo],
    ) -> Dict[str, Union[str, int]]:

        failure_type, material, failure_info = failure
        response = {
            'message': self.metadata.item_msg[failure_type],
            'item': material.name,
        }
        response[failure_type] = getattr(failure_info, failure_type)
        return response

    def format_properties(self) -> Dict[str, List[dict]]:
        return {
            'materials': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckPotentialTextures(Check, Properties):
    """
    Attempt to locate textures for materials, by multiple patterns.
    Will report failure if any required "slots" don't match any given pattern.
    """

    key = 'potentialTextures'
    version = (0, 1, 0)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[bpy.types.Material, Set[str]] = {}

    def run(self) -> Dict[bpy.types.Material, Set[str]]:
        """
        Returns any materials which had textures connected to forbidden slots,
        or textures were not connected where they were required to be.
        """
        if self.collector.input_file is None:
            return {}

        check_params = self.params.get('parameters', {})
        metadata_params = self.metadata.params.get('parameters', {})
        patterns = check_params.get('patterns', metadata_params['patterns'])
        required_slots = set(check_params.get('required', metadata_params['required']))

        patterns_runner = MultiTexPatterns(patterns)
        materials: List[bpy.types.Material] = self.collector.materials
        for mat_i, mat in enumerate(materials):
            matched_patterns = patterns_runner.all_matches(
                infile=self.collector.input_file,
                parse_sources={'matname': mat.name}
            )
            self.properties.append({
                'id': mat_i,
                'matches': matched_patterns,
            })
            missing_types = required_slots - matched_patterns.keys()
            if missing_types:
                self.failures[mat] = missing_types

        return self.failures

    def get_failures(self) -> Generator[Tuple[str, bpy.types.Material, Set[str]]]:
        for mat, missing_types in self.failures.items():
            for missing_type in sorted(missing_types):
                yield (mat, missing_type)

    def format_failure(
        self,
        failure: Tuple[bpy.types.Material, Set[str]],
    ) -> Dict[str, Union[str, int]]:
        material, failure_type = failure
        return {
            'message': self.metadata.item_msg,
            'item': material.name,
            'type': failure_type,
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        return {
            'materials': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckDisplayedUnitScale(Check, Properties):
    """
    Check if the units displayed in DCC match required units.
    """

    key = 'displayedUnits'
    version = (0, 1, 1)
    spec_unit_to_dcc = {
        'mm': 'millimeters',
        'cm': 'centimeters',
        'm': 'meters',
        'km': 'kilometers',
        'mile': 'miles',
        'foot': 'feet',
        'inch': 'inches'
    }

    def run(self) -> List[Tuple[str, str]]:
        """
        Return displayed and required units.
        Return displayed units in the scene to the property report.
        """
        desired_unit = self.spec_unit_to_dcc.get(
            self.params.get('parameters').get('desiredUnit').lower()
        )
        displayed_unit = bpy.context.scene.unit_settings.length_unit.lower()
        self.properties.append(displayed_unit)
        if not desired_unit:
            logger.warning('The required display unit "%s" is not available for selection in DCC,',
                           self.params.get('parameters').get('desiredUnit'))
        elif desired_unit != displayed_unit:
            self.failures.append((displayed_unit, desired_unit))

        return self.failures

    def format_failure(self, failure: Tuple[str, str]) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'expected': expected,
            'found': found,
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'displayedUnitScale': self.properties[0]
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        desired_unit = self.spec_unit_to_dcc.get(
            self.params.get('parameters').get('desiredUnit').lower()
        )
        return self.metadata.check_description.format(desired_unit)


@cgtcheck.runners.CheckRunner.register
class CheckSceneUnitScale(Check, Properties):
    """
    Check if the units scale in DCC match required units.
    """

    key = 'dccUnitScale'
    version = (0, 1, 1)
    units_multipliers = {
        'mm': 0.001,
        'cm': 0.01,
        'dm': 0.1,
        'm': 1,
        'km': 100,
        'foot': 0.304799998,
        'inch': 0.0253999998,
        'mile': 1609.3439893783,
        'yard': 0.9144
    }

    def run(self) -> List[Tuple[str, str]]:
        """
        Return units in scene and required units.
        Return units in scene to the property report.
        """
        float_tolerance = 0.001
        desired_unit = self.units_multipliers.get(
            self.params.get('parameters').get('desiredUnit').lower()
        )
        dcc_unit_scale = bpy.context.scene.unit_settings.scale_length
        self.properties.append(round(dcc_unit_scale, 9))
        if abs(desired_unit - dcc_unit_scale) > float_tolerance:
            self.failures.append((round(dcc_unit_scale, 9), desired_unit))

        return self.failures

    def format_failure(self, failure: Tuple) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'expected': str(expected),
            'found': str(found),
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'dccUnitScale': self.properties[0]
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        desired_unit = self.units_multipliers.get(
            self.params.get('parameters').get('desiredUnit').lower()
        )
        return self.metadata.check_description.format(desired_unit)


@cgtcheck.runners.CheckRunner.register
class CheckMaterialNames(Check, Properties):
    """
    Check if material names are proper in context of texture specification.
    """

    key = 'unparseableMaterialName'
    version = (0, 1, 0)

    def run(self) -> List[Tuple[str, str]]:
        """
        Returns incorrect material names paired with expected material names.
        """
        tex_paths = self.collector.mat_texture_path
        tex_spec = self.collector.tex_spec
        input_file = self.collector.input_file or ''

        tex_patterns = TexPatterns(tex_spec) if tex_spec else TexPatterns()

        for matname in tex_paths.keys():
            materials_name_id = {mat.name: self.collector.materials.index(mat) for
                                 mat in self.collector.materials}

            tex_patterns.reset_substitutions()
            try:
                tex_patterns.substitute(infile=input_file, matname=matname)
            except ParseError as exc:
                mat_name = exc.args[2]
                expected_mat_name = more_readable_re(exc.args[3])

                self.failures.append((mat_name, expected_mat_name))

                self.properties.append(
                    {
                        'material': materials_name_id[matname],
                        'expected': expected_mat_name,
                    }
                )

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'expected': str(expected),
            'found': str(found),
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        return {
            'materials': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckDccObjectTypes(Check, Properties):
    """
    Check type of objects present in the scene.
    """

    key = 'dccObjectTypes'
    version = (0, 2, 1)

    target_format_to_object_type = {'fbx': {
        'forbidMesh': ['MESH', 'CURVE', 'META', 'FONT', 'SURFACE'],
        'forbidNull': ['EMPTY', 'ARMATURE'],
        'forbidLight': ['LIGHT'],
        'forbidCamera': ['CAMERA'],
    }}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.properties: Dict[str, List[str]] = {}

    def run(self) -> List[Tuple[str, str]]:
        """
        Return a list of selected object types.
        """
        for obj in self.collector.fbx_exportable_objects:
            self.properties.setdefault(obj.type, []).append(obj.name)

        params = self.params.get('parameters', {})
        forbid_obj_types = self.target_format_to_object_type.get(params.get('target'), {})
        if forbid_obj_types:
            for obj in self.collector.fbx_exportable_objects:
                for key, obj_types in forbid_obj_types.items():
                    if params.get(key) and obj.type in obj_types:
                        self.failures.append(obj)
        else:
            logger.warning('Target file not found, check "dccObjectTypes" was skipped')

        return self.failures

    def format_failure(self, failure: Tuple) -> Dict[str, List[str]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            u'message': self.metadata.item_msg,
            u'item': failure.name,
            u'type': failure.type.capitalize()
        }

    def format_properties(self) -> Dict[str, List[str]]:
        """
        Format a property report.
        """
        return self.properties

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        params = self.params.get('parameters', {})
        forbidden_objects = []
        for key, is_enable in params.items():
            if is_enable is True:
                forbidden_objects.append(key.replace('forbid', ''))

        return self.metadata.check_description.format(', '.join(forbidden_objects))


DccObjectNameFailure = namedtuple('DccObjectNameFailure', 'type object expected')


@cgtcheck.runners.CheckRunner.register
class CheckDccObjectNames(Check, Properties):
    """
    Check objects names
    """

    key = 'dccObjectNames'
    version = (0, 1, 0)

    def run(self) -> List[DccObjectNameFailure]:
        """
        Returns failed items.
        """
        self.properties = {
            'objects': [obj.name for obj in self.collector.objects],
            'empties': [obj.name for obj in self.collector.empties]
        }
        params = self.params.get('parameters', {})
        uid_re = params.get('parsedVars').get('uid', '.+')
        insertable_values = {'uid': self.collector.uid}
        insertable_re = {'uid': uid_re}
        name_params = {
            'mesh': params.get('mesh', '.+'),
            'empty': params.get('empty', '.+'),
        }
        scene_nodes = {
            'empty': self.collector.empties,
            'mesh': self.collector.objects,
        }

        regex_groups = self.parse_regex_groups(insertable_re, insertable_values)
        bracket_groups = self.replace_bracket_groups(name_params, regex_groups, insertable_values)

        for node_type, nodes in scene_nodes.items():
            for node in nodes:
                node_name = node.name
                if node_type in bracket_groups:
                    match = re.match(bracket_groups[node_type], node_name)
                    if not match:
                        self.failures.append(
                            DccObjectNameFailure(node_type, node, bracket_groups[node_type])
                        )

        return self.failures

    @staticmethod
    def parse_regex_groups(
        patterns: Dict[str, str],
        strings: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """
        Get matching groups of regex from parsedArgs and a string, which can be
        UID or mesh name.

        Args:
            patterns (dict): parsedVars items, e.g.: {"uid": "(SM)_(\\w+)_LOD(\\d+)"}
            strings (dict): string to match to, e.g.: {"uid": "SM_Tabletop12_LOD0"}

        Returns:
            dict: found groups, e.g.: {"uid": ["SM", "Tabletop12", "0"]}
        """
        groups_dict = {}
        for var, pattern in patterns.items():
            groups = re.findall(pattern, strings[var])
            if groups:
                if type(groups[0]) == tuple:
                    groups = list(groups[0])
                groups_dict[var] = groups

        return groups_dict

    @staticmethod
    def replace_bracket_groups(
        patterns: Dict[str, str],
        groups: Dict[str, List[str]],
        fallback: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Replace bracketed groups, e.g. {uid} or {uid[0]} with the regex groups
        that were matched with parsedVars items already.

        Args:
            patterns (dict): strings with keywords inside brackets, to be replaced, e.g.:
                            {"regex": "^{uid}_{object[1]}(?:\\d{2}){0,}$"}
            groups (dict): keywords to replace the ones inside brackets, e.g.:
                        {'uid': ['Tabletop12', 'LOD0']}
            fallback (dict): original values, in case whole value is needed, e.g. for keyword w/o
                            index {uid}: {'uid': 'SM_Tabletop12_LOD0'}

        Returns:
            dict: return pattern with keyword(s) in brackets replaced, e.g.:
                {'regex': '^MI_BackyardTable12(?:\\d{2}){0,}$'}
        """
        new_patterns = {}
        for node_type, pattern in patterns.items():
            for var, group_list in groups.items():
                for i, group in enumerate(group_list):
                    grp = '{%s}' % var
                    grp_indexed = '{%s[%s]}' % (var, i)
                    if grp_indexed in pattern:
                        pattern = pattern.replace(grp_indexed, group)
                        new_patterns[node_type] = pattern
                    elif grp in pattern:
                        pattern = pattern.replace(grp, fallback[var])
                        new_patterns[node_type] = pattern
                    else:
                        new_patterns[node_type] = pattern

        return new_patterns

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check.
        """
        formatted_failures = (self.format_failure(f) for f in self.failures)
        return [f['message'].format(**f) for f in formatted_failures]

    def format_failure(self, failure: DccObjectNameFailure) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'type': failure.type.capitalize(),
            'expected': more_readable_re(failure.expected),
            'found': failure.object.name,
        }

    def format_properties(self) -> Dict[str, List[str]]:
        """
        Format a property report.
        """
        return self.properties


@cgtcheck.runners.CheckRunner.register
class CheckDccMaterialNames(Check, Properties):
    """
    Check whether material names match the requirements
    """

    key = 'dccMaterialNames'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, List[str]] = {}

    def run(self) -> Dict[str, List[str]]:
        params = self.params.get('parameters', {})
        uid = self.collector.uid
        param_regex = params.get('regex', '.+')
        var_uid = params.get('parsedVars').get('uid', '.+')
        var_object = params.get('parsedVars').get('object', '.+')
        materials_to_nodes, self.properties = self.get_mats_with_obj(self.collector.objects)
        spec_params = {
            'regex': param_regex,
        }
        parsed_vars = {
            'uid': var_uid,
            'object': var_object
        }

        for mat, nodes in materials_to_nodes.items():
            for node in nodes:
                strings = {'uid': uid, 'object': node}
                regex_groups = self.parse_regex_groups(parsed_vars, strings)
                bracket_groups = self.replace_bracket_groups(spec_params, regex_groups, strings)
                if bracket_groups:
                    match = re.match(bracket_groups['regex'], mat)
                    if not match:
                        self.failures.setdefault(mat, []).append(bracket_groups['regex'])
                else:
                    self.failures.setdefault(mat, []).append('')

        return self.failures

    @staticmethod
    def get_mats_with_obj(objects):
        """
        Get materials from scene objects.
        Get material list for each object
        Return dict where key is material and value is its object name(s).

        Args:
            objects (list): mesh objects

        Returns:
            dict: material name with its object(s) name(s), e.g.:
                  {'MI_BackyardTable1201': ['SM_BackyardTable1202', 'SM_BackyardTable1202']}
            dict: material list for each object for properties report
        """

        mat_obj_dict = {}
        properties = []
        for index, obj in enumerate(objects):
            mat_list = []
            for mat in obj.data.materials:
                mat_name = mat.name
                obj_name = obj.name
                mat_obj_dict.setdefault(mat_name, []).append(obj_name)
                mat_list.append(mat_name)
            properties.append(
                {
                    'id': index,
                    'materials': mat_list
                }
            )

        return mat_obj_dict, properties

    @staticmethod
    def parse_regex_groups(
        patterns: Dict[str, str],
        values: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """
        Get matching groups of regex from parsedArgs and a string, which can be
        UID or mesh name.

        Args:
            patterns (dict): parsedVars items, e.g.: {"uid": "(SM)_(\\w+)_LOD(\\d+)"}
            values (dict): string to match to, e.g.: {"uid": "SM_Tabletop12_LOD0"}

        Returns:
            dict: found groups, e.g.: {"uid": ["SM", "Tabletop12", "0"]}
        """
        groups_dict = {}
        for var, pattern in patterns.items():
            groups = re.findall(pattern, values[var])
            if groups:
                if type(groups[0]) == tuple:  # if it's list of tuples, make to list of strings
                    groups = list(groups[0])
                groups_dict[var] = groups

        return groups_dict

    @staticmethod
    def replace_bracket_groups(
        patterns: Dict[str, str],
        groups: Dict[str, List[str]],
        fallback: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Replace bracketed groups, e.g. {uid} or {uid[0]} with the regex groups
        that were matched with parsedVars items already.

        Args:
            patterns (dict): strings with keywords inside brackets, to be replaced, e.g.:
                            {"regex": "^{uid}_{object[1]}(?:\\d{2}){0,}$"}
            groups (dict): keywords to replace the ones inside brackets, e.g.:
                        {'uid': ['Tabletop12', 'LOD0']}
            fallback (dict): original values, in case whole value is needed, e.g. for keyword w/o
                            index {uid}: {'uid': 'SM_Tabletop12_LOD0'}

        Returns:
            dict: return pattern with keyword(s) in brackets replaced, e.g.:
                {'regex': '^MI_BackyardTable12(?:\\d{2}){0,}$'}
        """
        new_patterns = {}
        for node_type, pattern in patterns.items():
            for var, group_list in groups.items():
                for i, group in enumerate(group_list):
                    grp = '{%s}' % var
                    grp_indexed = '{%s[%s]}' % (var, i)
                    if grp_indexed in pattern:
                        pattern = pattern.replace(grp_indexed, group)
                        new_patterns[node_type] = pattern
                    elif grp in pattern:
                        pattern = pattern.replace(grp, fallback[var])
                        new_patterns[node_type] = pattern
                    else:
                        new_patterns[node_type] = pattern

        return new_patterns

    def get_failures(self) -> Tuple[str, str]:
        """
        Return an iterator of failures.
        """
        return ((mat, mat_val) for mat, mat_val in self.failures.items())

    def format_failure(self, failure: Tuple) -> Dict[str, Union[str, str]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'found': found,
            'expected': more_readable_re(expected[0]),
        }


@cgtcheck.runners.CheckRunner.register
class CheckUvUnwrapped(Check, Properties):
    """
    Check mesh objects for UV channels (at least one required).
    """

    key = 'uvUnwrappedObjects'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> Dict[Object, int]:
        """
        Return a list of objects which mesh contains less than one UV layer.
        Collect amount of UV layers per mesh for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            if obj.data and obj.data.uv_layers is not None:
                uv_amount = len(obj.data.uv_layers)
                self.properties.append({'id': i, 'uv_amount': uv_amount})
                if uv_amount < 1:
                    self.failures.append(obj.name)

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }
