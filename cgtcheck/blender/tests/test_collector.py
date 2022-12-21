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

from pathlib import Path

from cgtcheck.blender.collector import BlenderEntityCollector


class TestCollector:

    def test_object_collecting_only_selected_nothing_selected(
        self, create_basic_cube_and_monkey_head
    ):
        collector = BlenderEntityCollector()
        assert not collector.objects

        collector.collect(selection_only=True)
        assert not collector.objects

    def test_object_collecting_only_selected(
        self,
        multiple_objects_two_selected,
    ):
        collector = BlenderEntityCollector()
        assert not collector.objects

        collector.collect(selection_only=True)
        assert len(collector.objects) == 2
        expected = ['multiple_objects_two_selected_1', 'multiple_objects_two_selected_3']
        objects = [obj.name for obj in collector.objects]
        assert objects == expected

    def test_texture_paths_collecting_only_selected(
        self, multiple_objects_with_materials_two_selected
    ):
        collector = BlenderEntityCollector()
        assert not collector.mat_texture_path

        collector.collect(selection_only=True)
        assert len(collector.objects) == 2
        assert len(collector.mat_texture_path) == 2

        texture_names = [
            Path(path).name
            for mat_to_slots in collector.mat_texture_path.values()
            for path in mat_to_slots.values()
        ]
        expected = ['texture_1.png', 'texture_2.png', 'texture_5.png', 'texture_6.png']
        assert texture_names == expected

    def test_texture_paths_collecting_only_selected_nothing_selected(
        self, create_basic_cube_and_monkey_head
    ):
        collector = BlenderEntityCollector()
        assert not collector.mat_texture_path

        collector.collect(selection_only=True)
        assert not collector.mat_texture_path

    def test_materials_collecting_only_selected(
        self, multiple_objects_with_materials_two_selected
    ):
        collector = BlenderEntityCollector()
        assert not collector.materials

        collector.collect(selection_only=True)
        assert len(collector.objects) == 2
        assert len(collector.materials) == 2

        expected = [
            'multiple_objects_with_materials_two_selected_1',
            'multiple_objects_with_materials_two_selected_3',
        ]
        material_names = [mat.name for mat in collector.materials]
        assert expected == material_names

    def test_materials_collecting_only_selected_nothing_selected(
        self, create_basic_cube_and_monkey_head
    ):
        collector = BlenderEntityCollector()
        assert not collector.materials

        collector.collect(selection_only=True)
        assert not collector.materials

    def test_textures_collecting_only_selected(
        self, multiple_objects_with_materials_two_selected
    ):
        collector = BlenderEntityCollector()
        assert not collector.textures

        collector.collect(selection_only=True)
        assert len(collector.objects) == 2
        assert len(collector.textures) == 4

        texture_names = [
            texture.name
            for texture in collector.textures
        ]
        expected = ['texture_1.png', 'texture_2.png', 'texture_5.png', 'texture_6.png']
        assert texture_names == expected

    def test_textures_collecting_only_selected_nothing_selected(
        self, create_basic_cube_and_monkey_head
    ):
        collector = BlenderEntityCollector()
        assert not collector.textures

        collector.collect(selection_only=True)
        assert not collector.textures
