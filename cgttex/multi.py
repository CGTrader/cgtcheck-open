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
Classes which allow matching by multiple patterns.
May be very closely coupled with patterns.TexPatterns.

This module does not support Python2
"""

import os
from copy import copy
from typing import Dict, List, Set

import cgttex.patterns


class MultiTexPatterns:
    """
    Optimized TexPatterns variant for matching against multiple patterns.
    It can consume simpler patterns, only strictly requiring 'input_files'
    """

    def __init__(self, patterns: Dict[str, Dict]):
        patterns_adapted = {}
        for key in patterns:
            pattern = patterns_adapted[key] = copy(patterns[key])
            pattern['input_directories'] = ['\\.+']  # does not support filtering dir names
            pattern.setdefault('output_files', {})
            pattern.setdefault('parsed_variables', {})
            pattern.setdefault('predefined_variables', {})

        self.runners = {
            key: cgttex.patterns.TexPatterns(pattern=pattern)
            for key, pattern in patterns_adapted.items()
        }

    def all_matches(
        self,
        infile: str,
        parse_sources: Dict[str, str] = None
    ) -> Dict[str, List[str]]:
        """
        Returns all possible pattern matches.

        Note: Reimplements TexPatterns.find_textures.
        Will ignore specs regex 'input_directories'; entire tree is always searched.

        Args:
            infile: path to the "input" file to start search around
            parse_sources: dictionary of sources (type to source_string) for parse_variables
                           notable values: 'matname', 'outfile'

        Returns:
            Dict[asset_type, List[pattern_name]], pattern names are always sorted
        """
        if parse_sources is None:
            parse_sources = {}
        base_dir = os.path.dirname(infile)

        all_files = {
            f: os.path.join(dir, f)
            for dir, _dirs, files in os.walk(base_dir)
            for f in files
        }
        matches_by_pattern = {
            pattern_name: self.matches_for_runner(
                runner, infile, all_files, parse_sources=parse_sources
            ).keys()
            for pattern_name, runner in self.runners.items()
        }
        matches_by_type: Dict[str, Set[str]] = {}
        for pattern_name, matches in matches_by_pattern.items():
            for asset_type in matches:
                matches_by_type.setdefault(asset_type, set()).add(pattern_name)
        return {
            asset_type: sorted(patterns) for asset_type, patterns in matches_by_type.items()
        }

    @staticmethod
    def matches_for_runner(
        runner: cgttex.patterns.TexPatterns,
        infile: str,
        files: Dict[str, str],
        parse_sources: Dict[str, str] = None
    ) -> Dict[str, str]:
        """
        Returns found matches for given files and runner.

        Note that a single filepath could match multiple patterns,
        this is not the case with the single-pattern TexPatterns class.

        Return:
            Dict[type, filepath] - type of entry to matching file
        """
        runner.reset_substitutions()
        runner.substitute(infile=infile, **parse_sources)
        runner.compile()
        return {
            asset_type: filepath
            for filename, filepath in files.items()
            for asset_type, re_obj in runner.input_files.items()
            if re_obj.match(filename)
        }
