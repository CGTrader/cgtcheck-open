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
Module containing structures that can be used for optimizing mesh algorithms.
"""
from sys import float_info
from math import prod, nextafter, inf
from typing import List, Tuple, Dict, Union, Generator

import bpy
from mathutils import Vector

from .dimensions import get_bounding_box


class Grid:

    def build(self, obj):
        raise NotImplementedError()

    @staticmethod
    def create_box(
        min_coords: Union[Tuple[float, float, float], Vector],
        max_coords: Union[Tuple[float, float, float], Vector]
    ) -> bpy.types.Object:
        """
        Create a box that fits the given min_coords and max_coords.
        """
        bpy.ops.mesh.primitive_cube_add()
        box = bpy.context.active_object

        box.data.vertices[0].co = min_coords
        box.data.vertices[1].co = Vector((min_coords[0], min_coords[1], max_coords[2]))
        box.data.vertices[2].co = Vector((min_coords[0], max_coords[1], min_coords[2]))
        box.data.vertices[3].co = Vector((min_coords[0], max_coords[1], max_coords[2]))
        box.data.vertices[4].co = Vector((max_coords[0], min_coords[1], min_coords[2]))
        box.data.vertices[5].co = Vector((max_coords[0], min_coords[1], max_coords[2]))
        box.data.vertices[6].co = Vector((max_coords[0], max_coords[1], min_coords[2]))
        box.data.vertices[7].co = max_coords
        box.select_set(False)

        return box

    @staticmethod
    def is_point_inside(
        point: Union[Tuple[float, float, float], Vector],
        bbox: Tuple[
            Union[Tuple[float, float, float], Vector], Union[Tuple[float, float, float], Vector]
        ]
    ) -> bool:
        """
        Checks if the "point" is inside the "bbox",
        where "bbox" is 2 tuples containing the XYZ coordinates of
        the minimum and the maximum points of a bounding box.
        """
        x, y, z = point
        min_bbox, max_bbox = bbox
        x_min, y_min, z_min = min_bbox
        x_max, y_max, z_max = max_bbox
        is_inside = x_min <= x <= x_max and y_min <= y <= y_max and z_min <= z <= z_max
        return is_inside

    @staticmethod
    def get_bounding_boxes(
        obj,
        divisions: Tuple[int] = (10, 10, 10),
        obj_bounding_box: Tuple[Tuple[float, float, float], Tuple[float, float, float]] = None,
    ) -> List[Tuple[Vector, Vector]]:
        """
        Get a box grid that spans the object's entire bounding box (bbox), divided into "divisions".
        Returns the min & max coordinates of the boxes
        """
        if obj_bounding_box is None:
            obj_bounding_box = get_bounding_box([obj])
        bb_min, bb_max = obj_bounding_box
        bb_min_x, bb_min_y, bb_min_z = bb_min
        bb_max_x, bb_max_y, bb_max_z = bb_max

        x_section_length = (bb_max_x - bb_min_x) / divisions[0]
        y_section_length = (bb_max_y - bb_min_y) / divisions[1]
        z_section_length = (bb_max_z - bb_min_z) / divisions[2]

        box_start_end_vectors = []
        for z in range(divisions[2]):
            for y in range(divisions[1]):
                for x in range(divisions[0]):
                    x_new_start = bb_min[0] + x_section_length * x
                    y_new_start = bb_min[1] + y_section_length * y
                    z_new_start = bb_min[2] + z_section_length * z
                    x_new_end = x_new_start + x_section_length
                    y_new_end = y_new_start + y_section_length
                    z_new_end = z_new_start + z_section_length

                    start_vector = Vector((x_new_start, y_new_start, z_new_start))
                    end_vector = Vector((x_new_end, y_new_end, z_new_end))
                    box_start_end_vectors.append((start_vector, end_vector))

        return box_start_end_vectors


class FaceGrid(Grid):

    def __init__(self, obj: bpy.types.Object, divisions: Tuple[int, int, int] = None):
        """
        Args:
            obj: the object to construct a FaceGrid for. It is highly recommended to
                 work on an evaluated object, otherwise there's a risk of inconsistency between
                 object's bounding box, and the content in .data, sinve .data contents
                 are not adjusted by modifiers until you evalue it. Here's how to evaluate:
                 >>> depsgraph = bpy.context.evaluated_depsgraph_get()
                 >>> obj.evaluated_get(depsgraph)
            divisions: if an iterable with 3 ints is passed, the grid will be divided in this
                       many boxes along the X, Y, Z axis respectively. Otherwise these divisions
                       will be automatically decided based on number of polygons of the object.

        Example:
        >>> face_grid = FaceGrid(bpy.data.objects['Cube'])
        >>> face_grid.faces_per_non_empty_box
        {
            0: [0, 3, 4], 4: [0, 3, 5], 20: [0, 1, 4],
            24: [0, 1, 5], 100: [2, 3, 4], 104: [2, 3, 5],
            120: [1, 2, 4], 124: [1, 2, 5]
        }
        """
        if divisions is None:
            divisions = self.suggested_divisions(len(obj.data.polygons))
        (
            self.divisions,
            self.bounding_box,
            (self.len_x, self.len_y, self.len_z)
        ) = self._adjusted_for_small_length_axes(divisions, get_bounding_box([obj]))
        (self.g_min_x, self.g_min_y, self.g_min_z), _ = self.bounding_box

        self.faces_per_box: List[List[int]] = [[] for _ in range(prod(divisions))]
        self.world_verts = self.world_space_verts(obj)
        self.bounding_boxes = self.get_bounding_boxes(
            obj=obj, divisions=divisions, obj_bounding_box=self.bounding_box,
        )
        self.build(obj=obj)

    @staticmethod
    def suggested_divisions(polycount: int, target_per_box: int = 10) -> Tuple[int, int, int]:
        """
        Returns suggested divisions for a given poly count model.

        Args:
            polycount: total number of polygons of a model
            target_per_box: distribute this many per box; this counts ALL boxes, meaning this
                            number is not guaranteed, and actual number will be higher the higher
                            the polycount is
        """
        divs = max(1, int((polycount / target_per_box) ** (1 / 3)))
        return (divs,) * 3

    @staticmethod
    def _adjusted_for_small_length_axes(
        divisions: Tuple[int],
        bounding_box: Tuple[Tuple[float]],
    ) -> Tuple[Tuple[int], Tuple[Tuple[float]], List[float]]:
        """
        Adjusts bounding box, divisions and lengths for axis where length is close to zero.
        Intended to guard against floating point errors.

        Returns:
            [0] the adjusted divisions for this bounding box
            [1] the adjusted bounding_box
            [2] lengths of bounding_box axes
        """
        new_lengths = [0, 0, 0]
        new_divisions = list(divisions)
        new_bounding_box = [list(corner) for corner in bounding_box]
        for i, (div, (bb_min, bb_max)) in enumerate(zip(divisions, zip(*bounding_box))):
            new_lengths[i] = length = bb_max - bb_min
            far_value = max(abs(bb_min), abs(bb_max))
            # if using nextafter results in a subnormal float number,
            # we use float_info.min instead, which is the smallest normal value
            min_delta = max(nextafter(far_value, inf) - far_value, float_info.min) * div * 10
            if length < min_delta:
                new_lengths[i] = min_delta
                new_bounding_box[0][i] = bb_min - min_delta * 0.5
                new_bounding_box[1][i] = bb_max + min_delta * 0.5
                new_divisions[i] = 1

        return (
            tuple(new_divisions),
            tuple(map(tuple, new_bounding_box)),
            new_lengths,
        )

    @staticmethod
    def world_space_verts(obj: bpy.types.Object) -> List[Vector]:
        """
        Returns all vertices converted to worldspace. Indexes match.
        """
        obj_matrix_world = obj.matrix_world
        return [obj_matrix_world @ v.co for v in obj.data.vertices]

    def relevant_box_ids(
        self, bb_min: Tuple[float], bb_max: Tuple[float]
    ) -> Generator[int, None, None]:
        """
        Generator over box indexes which contain the given bounding box
        """
        divs = self.divisions
        len_x, len_y, len_z = self.len_x, self.len_y, self.len_z
        g_min_x, g_min_y, g_min_z = self.g_min_x, self.g_min_y, self.g_min_z

        # At which grid "step" the current bounding box value is
        bb_steps_min_x = int((bb_min[0] - g_min_x) / len_x * divs[0])
        bb_steps_min_y = int((bb_min[1] - g_min_y) / len_y * divs[1])
        bb_steps_min_z = int((bb_min[2] - g_min_z) / len_z * divs[2])
        bb_steps_max_x = int((bb_max[0] - g_min_x) / len_x * divs[0])
        bb_steps_max_y = int((bb_max[1] - g_min_y) / len_y * divs[1])
        bb_steps_max_z = int((bb_max[2] - g_min_z) / len_z * divs[2])
        # Prevent index error when polygon is exactly at bb limit
        x_range = range(
            min(bb_steps_min_x, divs[0] - 1),
            min(bb_steps_max_x, divs[0] - 1) + 1
        )
        y_range = range(
            min(bb_steps_min_y, divs[1] - 1),
            min(bb_steps_max_y, divs[1] - 1) + 1
        )
        z_range = range(
            min(bb_steps_min_z, divs[2] - 1),
            min(bb_steps_max_z, divs[2] - 1) + 1
        )
        for z in z_range:
            for y in y_range:
                for x in x_range:
                    yield x + y * divs[1] + z * divs[2] * divs[0]

    def polygon_bb(self, polygon: bpy.types.MeshPolygon) -> Tuple[Tuple[float], Tuple[float]]:
        """
        Returns world-space bounding box for a given polygon
        """
        world_verts = self.world_verts
        verts = [world_verts[i] for i in polygon.vertices]
        transposed_axis_values = tuple(zip(*verts))
        return (
            tuple(map(min, transposed_axis_values)),
            tuple(map(max, transposed_axis_values)),
        )

    def build(self, obj: bpy.types.Object):
        """
        Builds the face grid. Assigns it to "self.bounding_boxes".
        Calculates and assigns "self.faces_per_box" upon use.
        """
        faces_per_box = self.faces_per_box
        bounding_boxes = self.bounding_boxes
        relevant_box_ids = self.relevant_box_ids
        polygon_bb = self.polygon_bb
        intersects = self.intersects
        for poly in obj.data.polygons:
            relevant_boxes = list(relevant_box_ids(*polygon_bb(poly)))
            if len(relevant_boxes) < 3:
                for box_i in relevant_boxes:
                    faces_per_box[box_i].append(poly.index)
            else:
                for box_i in relevant_boxes:
                    box = faces_per_box[box_i]
                    bb = bounding_boxes[box_i]
                    if intersects(poly, bb):
                        box.append(poly.index)
        return faces_per_box

    def get_shared_boxes(self, face_indices: List[int]):
        """
        Returns the boxes the "face_indices" share.
        """
        face_indices_set = set(face_indices)
        common_boxes = []
        for box_index, faces in enumerate(self.faces_per_box):
            if face_indices_set.issubset(set(faces)):
                common_boxes.append(box_index)
        return common_boxes

    def boxes(self, include_empty: bool = False) -> List[Tuple[Vector, Vector]]:
        """
        Returns bounding boxes

        Args:
            include_empty: if True, will return all bounding boxes
        """
        return [
            self.bounding_boxes[box_index]
            for box_index, box_faces in enumerate(self.faces_per_box)
            if include_empty or box_faces
        ]

    def faces_per_non_empty_box(self) -> Dict[int, List[int]]:
        """
        Returns dictionary of box index to list of polygon indices which intersect the box
        """
        return {
            box_index: box_faces
            for box_index, box_faces in enumerate(self.faces_per_box)
            if box_faces
        }

    def visualize_boxes(self, include_empty: bool = False):
        """
        Create cubes in the scene, representing the grid boxes.
        """
        return [self.create_box(*box) for box in self.boxes(include_empty=include_empty)]

    @staticmethod
    def project(ref: Vector, normal: Vector, bbox: Tuple[Vector, Vector]) -> Tuple[Vector, Vector]:
        """
        A quick and rough projection to normal, counting from position.

        Args:
            ref: Reference point to project from.
            normal: Normal (axis) to project on.
            bbox: Bounding box.
        """
        bb_min, bb_max = bbox
        out_min = out_max = (bb_min - ref).dot(normal)
        projections = (
            (bb_max - ref).dot(normal),
            (Vector((bb_min.x, bb_min.y, bb_max.z)) - ref).dot(normal),
            (Vector((bb_min.x, bb_max.y, bb_min.z)) - ref).dot(normal),
            (Vector((bb_min.x, bb_max.y, bb_max.z)) - ref).dot(normal),
            (Vector((bb_max.x, bb_min.y, bb_min.z)) - ref).dot(normal),
            (Vector((bb_max.x, bb_min.y, bb_max.z)) - ref).dot(normal),
            (Vector((bb_max.x, bb_max.y, bb_min.z)) - ref).dot(normal),
        )
        for proj in projections:
            if proj < out_min:
                out_min = proj
            elif proj > out_max:
                out_max = proj

        return out_min, out_max

    @staticmethod
    def contains(bbox: Tuple[Vector, Vector], coord: Vector):
        """
        Returns whether the provided coord is contained within this 3D Box.
        """
        bb_min, bb_max = bbox
        return (
            bb_min.x <= coord.x <= bb_max.x
            and bb_min.y <= coord.y <= bb_max.y
            and bb_min.z <= coord.z <= bb_max.z
        )

    @staticmethod
    def overlaps(a_min, a_max, b_min, b_max):
        return not (a_max < b_min or a_min > b_max)

    def intersects(
        self,
        polygon: bpy.types.MeshPolygon,
        bbox: Tuple[Vector, Vector]
    ):
        """
        Checks if the "polygon" of "obj" intersects with "bbox".
        If the "polygon" is touching "bbox" or is within it, returns True. Otherwise, returns False.
        """
        world_verts = self.world_verts
        verts: List[Vector] = [world_verts[i] for i in polygon.vertices]

        # Test for Points inside bbox, if at least one is inside - intersection found
        for v in verts:
            if self.contains(bbox, v):
                return True

        # Test for separating planes along poly normals
        # Project BB vertices to axis (dot prod), see if BB and polygon projections overlap
        num_verts = len(verts)
        ref0 = verts[0]
        for i in range(num_verts - 1):
            norm = (verts[i] - ref0).cross((verts[i + 1] - ref0))
            min_proj, max_proj = self.project(ref0, norm, bbox)
            if max_proj < 0.0 or min_proj > 0.0:
                return False  # separation found, no intersection exists

        # Test for separating planes,
        # projecting to cross products of every polygon edge against every box normal
        axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
        for i in range(num_verts):
            ref = verts[i]  # reference point for 0.0
            edge = verts[(i + 1) % num_verts] - ref  # edge vector

            for j in range(3):
                norm = edge.cross(axes[j])

                # projecting box against cross product
                min_proj, max_proj = self.project(ref, norm, bbox)
                if min_proj <= 0.0 <= max_proj:
                    continue  # will always intersect if 0.0 is within interval;

                # project every other vert onto the cross product and check for overlap
                no_overlap = True
                for k in range(num_verts - 2):
                    vert = verts[(i + k + 2) % num_verts]
                    proj = (vert - ref).dot(norm)
                    if proj > 0.0:
                        overlaps_result = self.overlaps(0.0, proj, min_proj, max_proj)
                    else:
                        overlaps_result = self.overlaps(proj, 0.0, min_proj, max_proj)
                    if overlaps_result:
                        no_overlap = False  # skip the rest if there's at least one overlap
                if no_overlap:
                    return False  # triangle-box projections don't overlap, no intersection
        return True  # all projections overlap, intersection found
