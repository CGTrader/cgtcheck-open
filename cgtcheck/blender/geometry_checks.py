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

from collections import namedtuple, defaultdict
from itertools import combinations
from typing import List, Dict, Union, Tuple

import bmesh
import bpy
from bpy.types import Object
from mathutils import Vector

import threed.blender.common as bcommon
from threed.blender.structures import FaceGrid
from cgtcheck.common import Check, Properties
import cgtcheck
import cgtcheck.blender.collector


@cgtcheck.runners.CheckRunner.register
class CheckZeroFaceArea(Check, Properties):
    """
    Checks objects for zero-area faces.
    """

    key = 'zeroFaceArea'
    version = (0, 1, 2)
    THRESHOLD = 1e-10
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[Object, int] = {}

    def run(self) -> Dict[Object, int]:
        """
        Returns dict of objects that failed the check associated with number of failed faces.
        Collect information if the mesh has zero-area faces for the property report.
        """
        dcc_unit_scale = bpy.context.scene.unit_settings.scale_length
        threshold = self.THRESHOLD / dcc_unit_scale ** 2

        for i, obj in enumerate(self.collector.objects):
            bm = bmesh.new()
            bm.from_mesh(obj.data)

            num_failed_faces = 0
            for f in bm.faces:
                if f.calc_area() < threshold:
                    num_failed_faces += 1

            bm.free()
            self.properties.append({'id': i, 'zero_area_face': num_failed_faces})
            if num_failed_faces:
                self.failures[obj] = num_failed_faces

        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return [
            "{}: {}".format(obj.name, num_failed_faces)
            for obj, num_failed_faces in self.failures.items()
        ]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': 0,
            'found': self.failures[failed_obj],
        }


@cgtcheck.runners.CheckRunner.register
class CheckZeroLengthEdge(Check, Properties):
    """
    Checks objects for zero-length edges.
    """

    key = 'zeroLengthEdge'
    version = (0, 1, 2)
    THRESHOLD = 1e-10
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[Object, int] = {}

    def run(self) -> Dict[Object, int]:
        """
        Returns dict of objects that failed the check associated with number of failed edges.
        Collect information if the mesh has zero-length edges for the property report.
        """
        dcc_unit_scale = bpy.context.scene.unit_settings.scale_length
        threshold = self.THRESHOLD / dcc_unit_scale

        for i, obj in enumerate(self.collector.objects):
            bm = bmesh.new()
            bm.from_mesh(obj.data)

            num_failed_edges = 0
            for edge in bm.edges:
                if edge.calc_length() < threshold:
                    num_failed_edges += 1

            bm.free()
            self.properties.append({'id': i, 'zero_length_edge': num_failed_edges})

            if num_failed_edges:
                self.failures[obj] = num_failed_edges

        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return [
            "{}: {}".format(obj.name, num_failed_edges)
            for obj, num_failed_edges in self.failures.items()
        ]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': 0,
            'found': self.failures[failed_obj],
        }


@cgtcheck.runners.CheckRunner.register
class CheckZeroAngleFaceCorners(Check, Properties):
    """
    Checks objects for faces with zero-angle corners.
    """

    key = 'zeroAngleFaceCorners'
    version = (0, 1, 1)
    THRESHOLD = 1e-6
    format_properties = Properties._basic_format_properties

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[Object, int] = {}

    def run(self) -> Dict[Object, int]:
        """
        Returns dict of objects that failed the check associated with number of failed faces.
        Collect zero-angle corners count per mesh for properties report.
        """
        threshold = self.THRESHOLD

        for index, obj in enumerate(self.collector.objects):
            bm = bmesh.new()
            bm.from_mesh(obj.data)

            num_failed_faces = 0
            for f in bm.faces:
                numverts = len(f.verts)
                for i in range(numverts):
                    a = f.verts[i].co
                    b = f.verts[(i - 1) % numverts].co
                    c = f.verts[(i + 1) % numverts].co

                    # cos of angle between vectors equals dot product of the two normalized vectors
                    if abs(1.0 - (b - a).normalized().dot((c - a).normalized())) < threshold:
                        num_failed_faces += 1
                        break

            bm.free()
            self.properties.append({'id': index, 'zero_angle_corners': num_failed_faces})

            if num_failed_faces:
                self.failures[obj] = num_failed_faces

        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return [
            "{}: {}".format(obj.name, num_failed_faces)
            for obj, num_failed_faces in self.failures.items()
        ]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': 0,
            'found': self.failures[failed_obj],
        }


@cgtcheck.runners.CheckRunner.register
class CheckFacetedGeometry(Check, Properties):
    """
    Checks objects if they aren't fully faceted (all faces flat, or all hard edges).
    """

    key = 'facetedGeometry'
    version = (0, 2, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        """
        Returns list of objects that failed the check.
        Collect information if the mesh is fully faceted for the property report.
        """
        for obj_i, obj in enumerate(self.collector.objects):
            num_hard_vertices = 0
            obj.data.calc_normals_split()
            num_vertices = len(obj.data.vertices)

            normals_per_vertex = defaultdict(list)
            for loop in obj.data.loops:
                vtx_index = loop.vertex_index
                normals_per_vertex[vtx_index].append(loop.normal)

            for vertex_i in range(num_vertices):
                normals = normals_per_vertex.get(vertex_i, [])
                if len(normals) == 1:
                    continue
                for normal in normals:
                    dot_product = normal.dot(normals[0])
                    if abs(dot_product - 1.0) > 0.0001:
                        num_hard_vertices += 1
                        break

            faceted_geometry = num_hard_vertices == num_vertices
            self.properties.append({'id': obj_i, 'faceted': faceted_geometry})
            if faceted_geometry:
                self.failures.append(obj)

        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return ['{}'.format(f.name) for f in self.failures]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': False,
            'found': True,
        }


@cgtcheck.runners.CheckRunner.register
class CheckHardEdges(Check, Properties):
    """
    Checks objects for any hard edges.
    """

    key = 'noHardEdges'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        """
        Returns list of objects that failed the check.
        Collect information if the mesh has hard edges for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            has_hard_edges = any(edge.use_edge_sharp for edge in obj.data.edges)
            self.properties.append({'id': i, 'hard_edges': has_hard_edges})
            if has_hard_edges:
                self.failures.append(obj)

        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(f.name) for f in self.failures]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': False,
            'found': True,
        }


@cgtcheck.runners.CheckRunner.register
class CheckNGons(Check, Properties):
    """
    Checks objects for N-gons.
    """

    key = 'noNgons'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        """
        Returns list of objects that failed the check.
        Collect information if the mesh contains N-gons for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            has_ngons = any(len(polygon.vertices) > 4 for polygon in obj.data.polygons)
            self.properties.append({'id': i, 'ngons': has_ngons})
            if has_ngons:
                self.failures.append(obj)

        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(f.name) for f in self.failures]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name,
            'expected': False,
            'found': True,
        }


@cgtcheck.runners.CheckRunner.register
class CheckTriangleMaxCount(Check, Properties):
    """
    Check if scene exceeds triangle limit.
    """

    key = 'triangleMaxCount'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    tri_count_max = 90000

    def run(self) -> List[Tuple[str, int]]:
        """
        Return a list containing a string and triangle count if triangle count in the scene
        exceeds the 'maxTriCount'. Return empty list otherwise.
        Collect triangle count per mesh for properties report.
        """
        self.tri_count_max = self.params.get(
            'parameters', {}
        ).get(
            'triMaxCount', self.tri_count_max
        )
        tri_count = 0

        count_triangles = bcommon.mesh_triangle_count
        for i, obj in enumerate(self.collector.objects):
            tri_in_mesh = count_triangles(obj.data)
            tri_count += tri_in_mesh
            self.properties.append({'id': i, 'tri_count': tri_in_mesh})

        if tri_count > self.tri_count_max:
            self.failures = [('Model', tri_count)]

        return self.failures

    def fail_message(self, indent: str = '  ') -> str:
        """
        Returns failure message formatted as string.
        """
        return f'{self.metadata.msg} {self.tri_count_max}'

    def format_failure(self, failure: Tuple[str, int]) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        item, count = failure
        return {
            'message': self.metadata.item_msg,
            'item': item.capitalize(),
            'expected': self.tri_count_max,
            'found': count,
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        tri_count_max = self.params.get('parameters', {}).get('triMaxCount', self.tri_count_max)
        return self.metadata.check_description.format(str(tri_count_max))


@cgtcheck.runners.CheckRunner.register
class CheckEmbeddedTexturesFbx(Check, Properties):
    """
    Check if FBX file contains embedded textures.
    Collect texture index & whether it's embedded per object for properties report.
    """

    key = 'embeddedTexturesFbx'
    version = (0, 1, 0)

    def run(self) -> List[str]:
        """
        Return a list of embedded textures in FBX file.
        """
        self.collector: cgtcheck.blender.collector.BlenderEntityCollector

        for i, image in enumerate(self.collector.textures):
            if image is not None:
                is_packed = bool(image.packed_file)
                self.properties.append({'id': i, 'is_embedded': is_packed})
                if is_packed:
                    self.failures.append(image.name)

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }

    def format_properties(self) -> Dict[str, List[dict]]:
        """
        Format a property report.
        """
        return {
            'textures': self.properties
        }


@cgtcheck.runners.CheckRunner.register
class CheckOpenEdges(Check, Properties):
    """
    Checks objects for open edges.
    """

    key = 'openEdges'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        """
        Returns list of objects that failed the check.
        Collect information if the mesh contains open edges for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            has_open_edges = not all(edge.is_manifold for edge in bm.edges)
            if has_open_edges:
                self.failures.append(obj)
            bm.free()
            self.properties.append({'id': i, 'open_edges': has_open_edges})
        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return [f.name for f in self.failures]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name
        }


@cgtcheck.runners.CheckRunner.register
class CheckNonManifoldVertices(Check, Properties):
    """
    Checks objects for non-manifold vertices. Vertices that belong to wire and multiple face edges,
    isolated vertices, and vertices that belong to non-adjoining faces.
    """

    key = 'nonManifoldVertices'
    version = (0, 1, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Object]:
        """
        Returns list of objects that failed the check.
        Collect information if the mesh contains non-manifold vertices for the property report.
        """
        for i, obj in enumerate(self.collector.objects):
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            has_non_manifold_vertices = not all(vert.is_manifold for vert in bm.verts)
            if has_non_manifold_vertices:
                self.failures.append(obj)
            bm.free()
            self.properties.append({'id': i, 'non_manifold_vertices': has_non_manifold_vertices})
        return self.failures

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check
        """
        return [f.name for f in self.failures]

    def format_failure(self, failed_obj: Object) -> Dict[str, Union[str, bool]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failed_obj.name
        }


@cgtcheck.runners.CheckRunner.register
class CheckOverlappingFaces(Check, Properties):
    """
    Checks objects for overlapping coplanar faces.
    """
    key = 'overlappingFaces'
    version = (0, 2, 1)
    format_properties = Properties._basic_format_properties

    def run(self) -> List[Tuple[Object, List[List[int]]]]:
        """
        Returns list of objects and their overlapping face ids that failed the check.
        Collect information of mesh's overlapping face ids (if found) for the property report.
        """
        # Using absolute value may introduce problems, in that case use percentage of size of
        # scene's bounding box.
        threshold = 0.001

        depsgraph = bpy.context.evaluated_depsgraph_get()
        for obj in self.collector.objects:
            eval_obj = obj.evaluated_get(depsgraph)
            face_grid = FaceGrid(obj=eval_obj)
            total_overlapping_faces = set()
            for faces in face_grid.faces_per_box:
                if len(faces) < 2:
                    continue

                parallel_faces = self.get_faces_parallel(
                    obj=eval_obj, face_indices=faces, threshold=threshold
                )
                for poly_a, poly_b in parallel_faces:
                    if self.are_parallel_faces_coplanar(eval_obj, poly_a, poly_b, threshold):
                        if self._are_overlapping(eval_obj, poly_a, poly_b, threshold):
                            total_overlapping_faces.add((poly_a.index, poly_b.index))

            overlapping_faces_list = list(total_overlapping_faces)
            self.properties.append(
                {
                    'id': self.collector.objects.index(obj),
                    'overlapping_faces': overlapping_faces_list
                }
            )
            if total_overlapping_faces:
                self.failures.append((obj, overlapping_faces_list))

        return self.failures

    @staticmethod
    def get_faces_parallel(
        obj: bpy.types.Object,
        face_indices: List[int],
        threshold: float,
    ) -> List[List[int]]:
        """
        Returns a list of lists containing pairs of parallel faces' indices.
        Faces are considered parallel if difference between their tilt is within threshold.

        Args:
           obj: object to find faces in
           face_indices: indices of faces that should be checked
           threshold: acceptable tilt difference

        Example:
        Faces 0 and 8 are parallel to one another.
        Faces 3, 6 and 7 are parallel to one another.
        The result woill be [[0, 8], [3, 6], [3, 7], [6, 7]]
        """
        obj_data = obj.data
        parallel_faces = []
        for poly_a_index, poly_b_index in combinations(set(face_indices), 2):
            poly_a, poly_b = obj_data.polygons[poly_a_index], obj_data.polygons[poly_b_index]
            if 1.0 - abs(poly_a.normal.dot(poly_b.normal)) <= threshold:
                parallel_faces.append([poly_a, poly_b])

        return parallel_faces

    @staticmethod
    def are_parallel_faces_coplanar(
        obj: bpy.types.Object,
        poly_a: bpy.types.MeshPolygon,
        poly_b: bpy.types.MeshPolygon,
        threshold: float,
    ) -> bool:
        """
        Checks if two nearly parallel faces are close enough to be treated as coplanar.

        Args:
           obj: object to find vertices in
           poly_a: face that determines the plane
           poly_b: face which distance to poly_a should be checked
           threshold: value of distance that should not be exceeded for faces to be coplanar

        Returns:
            True if faces are almost copolanar, False otherwise
        """
        a_normal = poly_a.normal
        a_vert_co = obj.data.vertices[poly_a.vertices[0]].co
        b_verts_co = [obj.data.vertices[v].co for v in poly_b.vertices]

        projections = [a_normal.dot(vert - a_vert_co) for vert in b_verts_co]
        b_min = b_max = projections[0]
        for proj in projections[1:]:
            if proj > b_max:
                b_max = proj
            elif proj < b_min:
                b_min = proj

        if b_min <= 0 <= b_max:
            return True
        if abs(b_min) <= threshold or abs(b_max) <= threshold:
            return True

        return False

    @staticmethod
    def project(ref: Vector, axis: Vector, vertices: List[Vector]) -> Tuple[Vector, Vector]:
        """
        Projection to axis, counting from position.

        Args:
            ref: Reference point to project from.
            axis: axis to project on.
            vertices: vertices to project onto axis.
        """
        out_min = out_max = (vertices[0] - ref).dot(axis)
        projections = [
            (vertices[i] - ref).dot(axis) for i in range(1, len(vertices))
        ]
        for proj in projections:
            if proj < out_min:
                out_min = proj
            elif proj > out_max:
                out_max = proj

        return out_min, out_max

    @staticmethod
    def overlaps(a_min, a_max, b_min, b_max):
        return a_max > b_min and a_min < b_max

    def _are_overlapping(
        self,
        obj: bpy.types.Object,
        poly_a: bpy.types.MeshPolygon,
        poly_b: bpy.types.MeshPolygon,
        threshold: float,
    ) -> bool:
        """
        Checks if two faces are overlapping.

        Takes 2 almost coplanar faces defined by normal and list of vertices.
        Then uses separating axis theorem to check if its possible to find axis on which
        projections of faces are not overlapping. If such axis is found faces are marked
        as not overlapping. Axes that are checked are normals of all the edges of both faces.

        Args:
           obj: normal of first face
           poly_a: vertices of first face
           poly_b: normal of second face
           threshold: distance that should be exceeded for faces to be overlapping
        """
        project = self.project
        overlaps = self.overlaps
        a_verts = [obj.data.vertices[v].co for v in poly_a.vertices]
        b_verts = [obj.data.vertices[v].co for v in poly_b.vertices]

        axes = []
        for face_normal, verts, other_verts in [
            (poly_a.normal, a_verts, b_verts),
            (poly_b.normal, b_verts, a_verts),
        ]:
            num_verts = len(verts)
            for i in range(num_verts):
                ref = verts[i]  # reference point for 0.0
                edge = verts[(i + 1) % num_verts] - ref  # edge vector

                axis = edge.cross(face_normal)
                if axis in axes:
                    continue  # this axis was already checked and its not a separating axis
                axes.append(axis)

                # projecting second face against normal of chosen edge
                min_proj, max_proj = project(ref, axis, other_verts)
                # Using absolute threshold with projections in local coordinate system may cause
                # problems when objects is far away from world origin.
                min_proj = min_proj + threshold
                max_proj = max_proj - threshold
                if min_proj < 0.0 < max_proj:
                    continue  # projections of faces overlap if 0.0 is within interval;

                # project all other vertices(those not forming an edge) onto edge normal
                is_separating_axis = True
                for k in range(num_verts - 2):
                    proj = (verts[(i + k + 2) % num_verts] - ref).dot(axis)
                    if proj > 0.0:
                        is_overlapping = overlaps(0.0, proj, min_proj, max_proj)
                    else:
                        is_overlapping = overlaps(proj, 0.0, min_proj, max_proj)

                    if is_overlapping:
                        is_separating_axis = False  # skip the rest if there's at least one overlap
                        break
                if is_separating_axis:
                    return False  # separating axis found, faces are not overlapping
        return True  # faces overlap on all axes

    def list_failures(self) -> List[Object]:
        """
        Returns list of found issues for this check.
        """
        return [obj.name for obj, _faces in self.failures]

    def format_failure(
        self,
        failure: Tuple[Object, List[int]]
    ) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        obj, face_pairs = failure
        return {
            'message': self.metadata.item_msg,
            'item': obj.name,
            'overlapping_faces': ', '.join('"%s"' % str(fp) for fp in face_pairs)
        }


DccTrianglesRatioFailure = namedtuple('DccTrianglesRatioFailure', 'found comparator expected')


@cgtcheck.runners.CheckRunner.register
class CheckDccTrianglesRatio(Check, Properties):
    """
    Checks whether combined models' triangles-to-all-polygons ratio is within configured limits.
    """

    key = 'dccTrianglesRatio'
    version = (0, 1, 0)

    def run(self) -> List[DccTrianglesRatioFailure]:
        """
        Return triangles-to-all-polygons ratio along with expected values
        """
        triangles = 0
        all_polygons = 0

        params = self.params.get('parameters', {})
        threshold = float(params.get('threshold', '0.15'))
        comparator = params.get('comparator', '>')

        for obj in self.collector.objects:
            for poly in obj.data.polygons:
                if len(poly.vertices) == 3:
                    triangles += 1
            all_polygons += len(obj.data.polygons)

        in_ratio, calculated_ratio = self._is_triangles_ratio_condition_met(
            triangles, all_polygons, comparator, threshold
        )
        self.properties.append(calculated_ratio)

        if not in_ratio:
            self.failures.append(DccTrianglesRatioFailure(float(triangles) / float(all_polygons),
                                                          comparator, threshold))

        return self.failures

    @staticmethod
    def _is_triangles_ratio_condition_met(
        triangles: int,
        all_polygons: int,
        comparator: str,
        threshold: float
    ) -> Tuple[bool, float]:
        """
        Checks whether triangles to all polygons ratio is within configured limits,
        depending on configuration, it can mean higher or lower than the threshold.

        Args:
            triangles: number of tiangles in the model.
            all_polygons: number of polygons in the model.
            comparator: either '<' or '>' depending on configuration.
            threshold: value which should be compared to triangles ratio.

        Returns:
            bool: True if check should pass, False otherwise
            float: calculated ratio for report properties
        """

        if all_polygons == 0 and triangles == 0:
            return True, 1

        calculated_ratio = float(triangles) / float(all_polygons)

        if comparator == '<':
            return threshold < calculated_ratio, calculated_ratio
        else:
            return threshold > calculated_ratio, calculated_ratio

    def format_failure(self, failure: DccTrianglesRatioFailure) -> Dict[str, Union[str, float]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            u'message': self.metadata.item_msg,
            u'comparator': self.failures[0].comparator,
            u'found': format(float(self.failures[0].found), '.3f'),
            u'expected': format(float(self.failures[0].expected), '.3f'),
        }

    def format_details(self) -> Union[Dict[str, Union[str, bool]], None]:
        """
        Format a details report to be sent to Wildcat.
        Returns None if the check is not enabled to be reported as details.
        """
        if self.report_type != 'details':
            return None

        if self.failures:
            failed = True

        return {
            self.key: {
                'failed': failed,
                'text': (
                    u'Triangle ratio {} for models in FBX file is {} than the threshold: {}'.format(
                        format(float(self.failures[0].found), '.3f'),
                        self.failures[0].comparator,
                        format(float(self.failures[0].expected), '.3f')
                    )
                ),
                'title': u'Triangle ratio requirements is not fulfilled',
                'type': u'global',
            }
        }

    def format_properties(self) -> Dict[str, str]:
        """
        Format a property report.
        """
        return {
            'trianglesRatio': format(self.properties[0], '.3f')
        }

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        params = self.params.get('parameters', {})
        threshold = float(params.get('threshold', '0.15'))
        comparator = params.get('comparator', '>')

        return self.metadata.check_description.format(str(comparator), str(threshold))
