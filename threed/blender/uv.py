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

def polygon_area(verts):
    """
    Return the area of a 2d polygon (Shoelace formula)
    Works for concave and self-intersecting polygons

    verts    An array of polygon vertex coordinates in a form of [x, y]

    """

    n = len(verts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += verts[i][0] * verts[j][1]
        area -= verts[j][0] * verts[i][1]
    area = abs(area) / 2.0
    return area

def uv_faces_area(uvFaces, mesh, uvLayerIndex):
    """
    Return the total area of specified uv faces for the specified mesh and mesh uv layer
    """

    area = 0.0
    uvLayerData = mesh.uv_layers[uvLayerIndex].data
    for f in uvFaces:
        area += polygon_area([uvLayerData[i].uv for i in mesh.polygons[f].loop_indices])
    return area
