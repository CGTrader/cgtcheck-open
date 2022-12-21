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

import bpy
from typing import List, Dict
from cgtcheck.collector import EntityCollector


class BlenderEntityCollector(EntityCollector):

    def __init__(self, tex_paths=None, input_file=None, tex_spec=None, uid=None):
        super().__init__()

        self.objects: List[bpy.types.Object] = []
        self.empties: List[bpy.types.Object] = []
        self.lights: List[bpy.types.Object] = []
        self.cameras: List[bpy.types.Object] = []
        self.fbx_exportable_objects: List[bpy.types.Object] = []
        self.materials: List[bpy.types.Material] = []
        self.textures: List[bpy.types.Image] = []
        self.mat_texture_path: Dict[str, Dict[str, str]] = {}
        self.tex_paths = dict(sorted(tex_paths.items())) if tex_paths is not None else tex_paths
        self.input_file = input_file
        self.tex_spec = tex_spec
        self.uid = uid

    def collect(self, selection_only: bool = False):
        objects = [o for o in bpy.data.objects if o.select_get()] \
            if selection_only \
            else bpy.data.objects
        materials = set(
            slot.material for obj in objects for slot in obj.material_slots if slot.material
        )
        materials = sorted(materials, key=lambda m: m.name)
        self.objects = self.get_objects(objects)
        self.empties = self.get_empties(objects)
        self.lights = self.get_lights(objects)
        self.cameras = self.get_cameras(objects)
        self.fbx_exportable_objects = self.get_fbx_exportable_objects(objects)
        self.materials = self.get_materials(materials)
        self.textures = self.get_textures(materials)
        self.mat_texture_path = self.get_mat_texture_path(self.tex_paths, materials)
        self.tex_spec = self.get_tex_spec(self.tex_spec)
        self.uid = self.get_uid(self.uid)

    @staticmethod
    def get_objects(objects: List[bpy.types.Object]) -> List[bpy.types.Object]:
        return [obj for obj in objects if obj.type == 'MESH']

    @staticmethod
    def get_empties(objects: List[bpy.types.Object]) -> List[bpy.types.Object]:
        return [obj for obj in objects if obj.type == 'EMPTY']

    @staticmethod
    def get_lights(objects: List[bpy.types.Object]) -> List[bpy.types.Object]:
        return [obj for obj in objects if obj.type == 'LIGHT']

    @staticmethod
    def get_cameras(objects: List[bpy.types.Object]) -> List[bpy.types.Object]:
        return [obj for obj in objects if obj.type == 'CAMERA']

    @staticmethod
    def get_fbx_exportable_objects(objects: List[bpy.types.Object]) -> List[bpy.types.Object]:
        return [
            obj for obj in objects
            if obj.type in [
                'MESH', 'EMPTY', 'LIGHT', 'CAMERA', 'ARMATURE', 'CURVE', 'META', 'SURFACE', 'FONT'
            ]
        ]

    @staticmethod
    def get_materials(materials: List[bpy.types.Material]) -> List[bpy.types.Material]:
        return [mtl for mtl in materials]

    @staticmethod
    def get_textures(materials: List[bpy.types.Material]) -> List[bpy.types.Image]:
        materials_with_nodes = [
            m.node_tree.nodes for m in materials
            if m.node_tree
        ]
        image_nodes = [
            node for nodes in materials_with_nodes
            for node in nodes
            if hasattr(node, 'image')
        ]
        return [n.image for n in image_nodes if n is not None]

    @staticmethod
    def get_mat_texture_path(tex_paths, materials: List[bpy.types.Material]) -> Dict[str, Dict]:

        if tex_paths is not None:
            return tex_paths

        def get_linked_texture_files(input, filepaths=None):
            if filepaths is None:
                filepaths = []

            for link in input.links:
                if link.from_node.type == "TEX_IMAGE" and link.from_node.image \
                        and link.from_node.image.filepath:
                    filepaths.append(
                        bpy.path.abspath(
                            link.from_node.image.filepath,
                            library=link.from_node.image.library
                        )
                    )
                else:
                    for input in link.from_node.inputs:
                        get_linked_texture_files(input, filepaths=filepaths)
            return filepaths

        texture_paths = {}
        input_name_conversion = {
            'Base Color': 'color',
            'Alpha': 'opacity'
        }
        for material in materials:
            texture_paths[material.name] = {}
            if not material.node_tree:
                continue

            texture_occlusion_path = None
            for link in material.node_tree.links:
                if link.to_node.type == 'OUTPUT_MATERIAL':
                    material_node = link.from_node
                elif link.from_node.label == 'OCCLUSION':
                    texture_occlusion_path = bpy.path.abspath(
                        link.from_node.image.filepath, library=link.from_node.image.library
                    )

            for input in material_node.inputs:
                input_name = input.name.lower()
                if input.name in input_name_conversion:
                    input_name = input_name_conversion.get(input.name)

                filepaths = get_linked_texture_files(input)
                if filepaths:
                    mat_textures = texture_paths[material.name]
                    mat_textures[input_name] = filepaths[0]

            if texture_occlusion_path:
                texture_paths[material.name]['occlusion'] = texture_occlusion_path

        return texture_paths
