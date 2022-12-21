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
This is a base collector that is meant to be inherited & have its methods overloaded.
"""


class EntityCollector:

    def __init__(self, tex_paths=None, input_file=None, tex_spec=None, uid=None):
        self.objects = []
        self.empties = []
        self.lights = []
        self.cameras = []
        self.fbx_compatible_objects = []
        self.mat_texture_path = {}
        self.tex_paths = tex_paths
        self.input_file = input_file
        self.tex_spec = tex_spec
        self.uid = uid

    def collect(self, selection_only=False):
        self.objects = self.get_objects()
        self.empties = self.get_empties()
        self.lights = self.get_lights()
        self.cameras = self.get_cameras()
        self.fbx_compatible_objects = self.get_fbx_compatible_objects()
        self.tex_spec = self.get_tex_spec(self.tex_spec)
        self.mat_texture_path = self.get_mat_texture_path(self.tex_paths)
        self.uid = self.get_uid(self.uid)

    @staticmethod
    def get_objects():
        # type: () -> list
        """
        This is a dummy method. It's meant to be overwritten.
        """
        return list()

    @staticmethod
    def get_empties():
        # type: () -> list
        """
        This is a dummy method. It's meant to be overwritten.
        """
        return list()

    @staticmethod
    def get_lights():
        # type: () -> list
        """
        This is a dummy method. It's meant to be overwritten.
        """
        return list()

    @staticmethod
    def get_cameras():
        # type: () -> list
        """
        This is a dummy method. It's meant to be overwritten.
        """
        return list()

    @staticmethod
    def get_fbx_compatible_objects():
        # type: () -> list
        """
        This is a dummy method. It's meant to be overwritten.
        """
        return list()

    @staticmethod
    def get_mat_texture_path(tex_paths):
        # type: (dict) -> dict[str, list]
        """
        This is a method to provide tex_paths to checks.
        Can be overwritten to gather information from the scene instead.
        """
        if tex_paths is not None:
            return tex_paths
        else:
            return {}

    @staticmethod
    def get_tex_spec(tex_spec):
        # type: (dict) -> dict
        if tex_spec is not None:
            return tex_spec
        else:
            tex_spec = {
                'input_files': {},
                'output_files': {},
                'parsed_variables': {},
                'required_textures': [],
                'input_directories': [],
                'predefined_variables': {}
            }
            return tex_spec

    @staticmethod
    def get_uid(uid):
        # type: (str) -> str
        if uid is not None:
            return uid
        else:
            return ''
