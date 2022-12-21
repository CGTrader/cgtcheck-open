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

from __future__ import (division, print_function, absolute_import, unicode_literals)

"""
Contains various Blender scene and object validation functionality.
"""

import logging
import bmesh

logger = logging.getLogger(__name__)

def zero_area_faces(objects, threshold=1e-10):
    """
    Checks objects for zero-area faces.

    Args:
        objects (list):    objects to process, should be mesh objects
        threshold (float): minimum allowed face area

    Returns:
        (dict) failed objects, keys are objects, values are numbers of failed faces
    """

    failed_objects = {}
    for obj in objects:
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        num_failed_faces = 0
        for f in bm.faces:
            if f.calc_area() < threshold:
                num_failed_faces += 1

        bm.free()

        if num_failed_faces:
            failed_objects[obj] = num_failed_faces

    return failed_objects

def zero_length_edges(objects, threshold=1e-10):
    """
    Checks objects for zero-length edges.

    Args:
        objects (list):    objects to process, should be mesh objects
        threshold (float): allowed minimum edge length

    Returns:
        (dict) failed objects, keys are objects, values are numbers of failed edges
    """

    failed_objects = {}
    for obj in objects:
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        num_failed_edges = 0
        for edge in bm.edges:
            if edge.calc_length() < threshold:
                num_failed_edges += 1

        bm.free()

        if num_failed_edges:
            failed_objects[obj] = num_failed_edges

    return failed_objects

def zero_angle_face_corners(objects, threshold=1e-6):
    """
    Checks objects for faces with zero-angle corners.

    Args:
        objects (list):    objects to process, should be mesh objects
        threshold (float): allowed value deviation in terms of cos(angle)

    Returns:
        (dict) failed objects, keys are objects, values are numbers of failed faces
    """

    failed_objects = {}
    for obj in objects:
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        num_failed_faces = 0
        for f in bm.faces:
            numverts = len(f.verts)
            for i in range(numverts):
                a = f.verts[i].co
                b = f.verts[(i - 1) % numverts].co
                c = f.verts[(i + 1) % numverts].co

                if abs(1.0 - (b - a).normalized().dot((c - a).normalized())) < threshold:
                    num_failed_faces += 1
                    break

        bm.free()

        if num_failed_faces:
            failed_objects[obj] = num_failed_faces

    return failed_objects


def faceted_geometry(objects):
    """
    Checks objects if they aren't fully faceted (all faces flat, or all hard edges).

    Args:
        objects (list):    objects to process, should be mesh objects

    Returns:
        (list) faceted objects
    """

    faceted_objects = []
    for obj in objects:
        if all(edge.use_edge_sharp for edge in obj.data.edges):
            faceted_objects.append(obj)

    return faceted_objects
