# -*- coding: utf-8 -*-

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
This module contains code for finding texture files according to a naming convention.
"""

from __future__ import (division, print_function, absolute_import, unicode_literals)

import re
import os
import json
import logging
from pprint import pformat

logger = logging.getLogger(__name__)

REQUIRED_TEXTURES = ["color", "metallic", "roughness", "normal", "occlusion"]

PATTERN_TEMPLATES = {
    'giraffe': {
        'spec_name': 'Giraffe 1.0.0',

        'predefined_variables': {},
        'parsed_variables': {
            # capture digits, optionally prefixed with M_0_ or M_ (which itself isn't captured)
            'matid':  r'^(?:M_0_|M_)?(\d+)$',
        },

        # matches: tex, texture and textures (case-insensitivity passed as flag by default)
        'input_directories': ['^tex(?:ture[s]?)]?$'],
        'required_textures': REQUIRED_TEXTURES,

        # The following are frequently used special substitutions, which have known sources,
        # and are available as long as their sources are supplied to substitute(parse_sources=):
        #   {infilename}    -- source: 'infile'     -- input filename without extension
        #   {infileext}     -- source: 'infile'     -- input filename extension, without leading '.'
        #   {outfilename}   -- source: 'outfile'    -- output filename without extension
        #   {outfileext}    -- source: 'outfile'    -- filetype extension of output file, without leading '.'  # noqa E501
        #   {fileid}        -- source: 'infilename' -- parsed id from (input) filename
        #   {matid}         -- source: 'matname'    -- parsed if from material name
        'input_files': {
            'color':      r'^M_0_{matid}_{infilename}_{matid}_BaseColor.\w+$',
            'roughness':  r'^M_0_{matid}_{infilename}_{matid}_Roughness.\w+$',
            'metallic':   r'^M_0_{matid}_{infilename}_{matid}_Metalness.\w+$',
            'normal':     r'^M_0_{matid}_{infilename}_{matid}_Normal.\w+$',
            'emission':   r'^M_0_{matid}_{infilename}_{matid}_Emissive.\w+$',
            'occlusion':  r'^M_0_{matid}_{infilename}_{matid}_AO.\w+$',
            'opacity':    r'^M_0_{matid}_{infilename}_{matid}_Opacity.\w+$',
        },

        # output_files have additional replacement strings,
        # which are only replaced in get_filename(typestr, ext):
        #   {ext}  -- desired texture file extension
        'output_files': {
            'color':      'M_0_{matid}_{infilename}_{matid}_BaseColor.{ext}',
            'roughness':  'M_0_{matid}_{infilename}_{matid}_Roughness.{ext}',
            'metallic':   'M_0_{matid}_{infilename}_{matid}_Metalness.{ext}',
            'normal':     'M_0_{matid}_{infilename}_{matid}_Normal.{ext}',
            'emission':   'M_0_{matid}_{infilename}_{matid}_Emissive.{ext}',
            'occlusion':  'M_0_{matid}_{infilename}_{matid}_AO.{ext}',
            'ORM':        'M_0_{matid}_{infilename}_{matid}_ORM.{ext}',
            'specular':   'M_0_{matid}_{infilename}_{matid}_Specular.{ext}',
            'glossiness': 'M_0_{matid}_{infilename}_{matid}_Glossiness.{ext}',
            'opacity':    'M_0_{matid}_{infilename}_{matid}_Opacity.{ext}'
        }
    },
    'generic': {
        'spec_name': 'Generic 1.0.0',

        'predefined_variables': {},
        'parsed_variables': {
            'fileid':     r'^([^_]+)?_.*',             # capture everything before first underscore
            'matid':      r'^([^-_]+)[-]*([^-_]+).*',  # capture up to two groups before underscore,
                                                       # optionally delimited by '-' (not captured)
        },

        'required_textures': REQUIRED_TEXTURES,
        'input_directories': ['^tex(?:ture[s]?)]?$'],  # matches: tex, texture and textures
                                                       # (case-insensitivity passed as flag by default)  # noqa E501

        'input_files': {
            'color':      r'^{matid}_BaseColor.\w+$',
            'roughness':  r'^{matid}_Roughness.\w+$',
            'metallic':   r'^{matid}_Metalness.\w+$',
            'normal':     r'^{matid}_Normal.\w+$',
            'emission':   r'^{matid}_Emissive.\w+$',
            'occlusion':  r'^{matid}_AO.\w+$',
        },

        'output_files': {
            'color':      '{matid}_BaseColor.{ext}',
            'roughness':  '{matid}_Roughness.{ext}',
            'metallic':   '{matid}_Metalness.{ext}',
            'normal':     '{matid}_Normal.{ext}',
            'emission':   '{matid}_Emissive.{ext}',
            'occlusion':  '{matid}_AO.{ext}',
            'ORM':        '{matid}_ORM.{ext}',
            'specular':   '{matid}_Specular.{ext}',
            'glossiness': '{matid}_Glossiness.{ext}',
            'opacity':    '{matid}_Opacity.{ext}'
        }
    },
}


class ParseError(Exception):
    """Gets raised if failed to parse regular expression"""
    pass


class MissingSourceError(ParseError):
    """Raised if source was not supplied for parsing or substitution"""
    pass


class MissingParseVariableError(ParseError):
    """Raised if was asked to parse a non-existing parse variable"""
    pass


class PatternEntry(object):
    """
    Minimal object for holding original string and caching substitutions.
    Provides functionality related to substitutions.
    """

    __slots__ = 'raw', 'substituted'

    def __init__(self, raw, substituted=None):
        self.raw = raw
        self.substituted = substituted

    def substitute(self, strict=True, return_only=False, **substitutes):
        """
        Substitutes given string tokens and returns resulting string.
        Optionally updates instances substituted field.

        Args:
            strict:         if True, required but not supplied tokens raise an exception;
                            otherwise token is skipped
            return_only:    if True, this instance's .substituted field will not be updated
            **substitutes:

        Return:
            string with tokens substituted

        Raises:
            MissingParseSourceError: on strict=True and required token not supplied
        """

        filled = None
        if strict:
            try:
                filled = self.get().format(**substitutes)
            except KeyError:
                raise MissingSourceError(
                    'Variable to substitute was not supplied',
                    self.raw, substitutes,
                )
        else:
            filled = self.get()
            for key, value in substitutes.items():
                filled = filled.replace('{{{}}}'.format(key), value)

        if not return_only:
            self.substituted = filled

        return filled

    def unescape_substitute(self, substituted=''):
        unescaped_substituted = re.sub(r'\\(.)', r'\1', substituted or self.substituted)
        return unescaped_substituted

    def get(self):
        """Returns substituted value if available, otherwise returns raw"""

        return self.substituted or self.raw

    def reset(self):
        """Resets substituted value"""

        self.substituted = None

    def __hash__(self):
        return hash(self.raw)

    def __eq__(self, other):
        return self.raw == other.raw

    def __ne__(self, other):
        return self.raw != other.raw


class RegexEntry(PatternEntry):
    """Expanded PatternEntry variant providing regex functionality"""

    __slots__ = 'compiled', 'flags'

    def __init__(self, raw, substituted=None, compiled=None, flags=re.IGNORECASE):
        super(RegexEntry, self).__init__(raw, substituted)
        self.compiled = compiled
        self.flags = flags

    def compile(self):
        """Compiles and caches the regular expression"""

        self.compiled = re.compile(self.get(), flags=self.flags)

    def reset(self, compiled=True):
        """Resets substitutions, and compiled cache (optional)"""

        super(RegexEntry, self).reset()
        if compiled:
            self.compiled = None

    def match(self, content):
        """Returns a regex match object (or None, on failed to match) for given content"""

        if not self.compiled:
            self.compile()
        return self.compiled.match(content)

    def parse(self, content):
        """Returns parsed and concatenated result (or None, on failed to match) for given content"""

        match = self.match(content)
        return ''.join(match.groups()) if match else None


class TexPatterns(object):
    """
    Class for texture filename discovery based on naming patterns.
    Different projects are likely to have different patterns.

    The pattern matching requires two steps:
    1. replacing special strings in regular expressions (e.g. "{somevalue}") is handled by
       .substitute() function before matching begins
    2. regular expression matching takes place during .find_textures(), but it has an optional
       parameter refreshRe=, which if True (default) will take care of step 1 automatically)

    As a result, common usage scenario looks like the following:
    tp = textures.TexPattern()
    textures = tp.find_textures(
        infile=r'full/path/to/some/input/file.fbx',
        matname='some_material_name'
    )
    """

    _default_pattern = PATTERN_TEMPLATES['giraffe']

    def __init__(self, pattern=_default_pattern, compile=True):

        self.full_pattern = pattern

        self.predefined_variables   = pattern['predefined_variables']
        self.input_directories      = [RegexEntry(v) for v in pattern['input_directories']]
        self.input_files            = {k: RegexEntry(v)   for k, v in pattern['input_files'].items()}  # noqa: E501
        self.parsed_variables       = {k: RegexEntry(v)   for k, v in pattern['parsed_variables'].items()}  # noqa: E501
        self.output_files           = {k: PatternEntry(v) for k, v in pattern['output_files'].items()}  # noqa: E501
        self.technical_requirements = pattern.get('technical_requirements') or None

        if 'required_textures' in pattern:
            self.required_textures = pattern['required_textures']
        else:
            self.required_textures = REQUIRED_TEXTURES

        if compile:
            self.compile()

    def parse(self, variable, content, flags=re.IGNORECASE):
        """
        Parses a variable from a given source string.
        All capture groups are concatenated to get the result.

        Args:
            variable: name of the variable to parse for
            content:  source string to parse from
            flags:    regex flags to use when parsing regular expressions (disabled)

        Raises:
            ParseError: if regex did not match for given source
            MissingParseVariableError: if asked to parse an unknown variable (missing in pattern)

        Return:
            None if variable not provided, string of concatenated regex groups on success
        """

        re_obj = self.parsed_variables.get(variable, None)
        if re_obj:
            match = re_obj.match(content)
            if match and match.groups():
                return ''.join(match.groups())

            raise ParseError('Failed to parse', variable, content, re_obj.get())

        raise MissingParseVariableError('The requested parse variable was not in spec',
                                        (variable, content, self.full_pattern))

    def compile(self, flags=re.IGNORECASE):
        """
        Compiles regular expressions.
        Call this function after changing any regular expression properties.
        Note that unless substitute() is called beforehand,
        the special strings will not be substituted in compiled regexes.
        """

        all_regex_entries = (
            self.input_directories
            + list(self.input_files.values())
            + list(self.parsed_variables.values())
        )
        for entry in all_regex_entries:
            entry.compile()

    def substitute(self, flags=re.IGNORECASE, escape_special=True, **parse_sources):
        """
        Does any special string substitutions in own regular expression entries.

        The following are predefined substitutions, which have known sources, and are available
        as long as their sources are supplied:
            {infilename}    -- source: 'infile'     -- input filename without extension
            {infileext}     -- source: 'infile'     -- input filename extension, without leading '.'
            {outfilename}   -- source: 'outfile'    -- output filename without extension
            {outfileext}    -- source: 'outfile'    -- file extension of output file, no leading '.'
            {fileid}        -- source: 'infilename' -- parsed id from (input) filename
            {matid}         -- source: 'matname'    -- parsed if from material name

        Args:
            flags:           regular expression flags to use for parsing
            **parse_sources: any sources for parsed_variables (passed as named parameters,
                             or splatted), key names matching the variable names, it is
                             recommended to always pass sources for: 'infile', 'outfile'
                             and 'matname', as special predefined substitutions depend on them

        Return:
            TexPatterns instance with substitutions applied
            (same instance as set to self._substituted)

        Raises:
            MissingSourceError:   if token required by string was not supplied in sources
            MissingParseVariable: if token required by string is defined in specification
        """

        required = set()
        for re_obj in list(self.input_files.values()) + list(self.output_files.values()):
            required.update(set(re.findall(r'\{(\w*)\}', re_obj.raw)))
        required.discard('ext')   # special case, inserted by generate_filename()

        # Predefined_variables are ready for replacements
        prepared = dict(self.predefined_variables)
        required = required.difference(set(prepared))  # remove predefined variables from required

        # Replacements with alternative sources (to do: can probably be abstracted)
        fileid_required = 'fileid' in required
        filename_required = ('infilename' in required) or ('infileext' in required)
        if 'infile' in parse_sources and (fileid_required or filename_required):
            base_infile = os.path.basename(parse_sources['infile'])
            (prepared['infilename'], prepared['infileext']) = os.path.splitext(base_infile)

            # Special Symbols in filename Workaround
            if escape_special:
                escaped_filename = {'infilename': re.escape(prepared['infilename'])}
                prepared.update(escaped_filename)

            required.discard('infilename')
            required.discard('infileext')

            if fileid_required:
                prepared['fileid'] = self.parse('fileid', prepared['infilename'])
                required.remove('fileid')

        if 'outfile' in parse_sources and ('outfilename' in required or 'outfileext' in required):
            base_outfile = os.path.basename(parse_sources['outfile'])
            (prepared['outfilename'], prepared['outfileext']) = os.path.splitext(base_outfile)
            required.discard('outfilename')
            required.discard('outfileext')

        if 'matname' in parse_sources and 'matid' in required:
            prepared['matid'] = self.parse('matid', parse_sources['matname'])
            required.remove('matid')

        # Remaining direct replacements
        for name in required:
            if name in self.parsed_variables:
                src = parse_sources.get(name, None)
                if src is None:
                    raise MissingSourceError('Source was not provided for variable', name)
                else:
                    prepared[name] = self.parse(name, src)
            else:
                raise MissingParseVariableError(
                    'Variable is required in replacements, but its definition is missing', name
                )

        for entry in self.input_files.values():
            entry.substitute(strict=True, **prepared)   # raises on any missing replacements

        for entry in self.output_files.values():
            entry.substitute(strict=False, **prepared)  # leave {ext} in

    def reset_substitutions(self):
        """
        Reset all input and output substitution entries to their original values (from pattern)
        """

        for entry in list(self.input_files.values()) + list(self.output_files.values()):
            entry.reset()

    def generate_filename(
        self,
        type,
        ext='png',
        fallback='texture',
        from_output_files=True,
        remove_escape_symbols=True,
    ):
        """
        Returns a filename for a given file type and extension, as defined in output_files.
        If from_output_files if False, then returns filename from input_files.

        WARNING: don't forget to call substitute() beforehand, to replace the higher level
        substitutions like matid, otherwise only {ext} will be replaced.

        Args:
            typekey:    texture type string, as used by non-template texture RE attributes
                        ('color', 'roughness', etc.)
            ext:        filename extension string (with leading period)
            fallback:   generic filename to use if type is not available; if a falsy value is
                        supplied, will MissingParseVariable exception instead
            remove_escape_symbols: if this flag is set to True, backslashes are removed.
        Returns:
            expected filename of a given texture type
        """

        if from_output_files:
            files = self.output_files
        else:
            files = self.input_files

        if type in files:
            substituted = files[type].substitute(ext=ext, strict=False, return_only=True)
            if remove_escape_symbols:
                return files[type].unescape_substitute(substituted=substituted)
            else:
                return substituted
        elif fallback:
            return '{}.{}'.format(fallback, ext)
        else:
            raise MissingParseVariableError('Pattern not found for file type', type)

    def find_single_texture(self, files, types):
        """
        Attempts to find first regex-matching file for given type.
        Returns (file, type, match_object) on success, None otherwise.
        """

        for type in types:
            re_obj = self.input_files.get(type, None)
            if re_obj:
                for f in files:
                    match = re_obj.match(f)
                    if match:
                        return (f, type)

        return None

    def find_textures(
        self,
        infile,
        parse_sources={},
        flags=re.IGNORECASE,
        refresh_re=True,
        abs_paths=True
    ):
        """
        Attempts to locate any texture files matching the patterns.

        Args:
            infile:        absolute or relative path to input file
            matname:       [optional, but recommended] name of the relevant material
            flags:         regular expression flags to use for parsing
            refresh_re:    if true, recompile and subsittute regular expressions before search
            abs_paths:     stores full path to textures if True, otherwise stores only filename
            parse_sources: dictionary of sources (type to source_string) for parse_variables

        Returns:
            Dictionary with found textures, any missing ones will have None value

        Raises:
            MaterialNameError: if the index could not be extracted from material name using re_matid
        """

        if refresh_re:
            self.reset_substitutions()
            self.substitute(infile=infile, **parse_sources)
            self.compile(flags=flags)

        found = {}
        to_find = dict(self.input_files)
        indir = os.path.dirname(infile)
        for pdir, dirs, files in os.walk(indir):
            for f in files:
                for type, re_obj in to_find.items():
                    if re_obj.match(f) and (type.lower() != "fbx"):
                        found[type] = os.path.join(pdir, f) if abs_paths else f
                        to_find.pop(type, None)
                        break

            # filter directories to recurse into
            dirs[:] = [
                d for d in dirs
                if any((re_obj_dir.match(d) for re_obj_dir in self.input_directories))
            ]

        return found

    def save(self, filepath):
        """Save pattern to JSON file. Substitutions are not saved."""

        with open(filepath, 'w') as f:
            f.write(json.dumps(self.full_pattern))

    def load(self, filepath, compile=True):
        """Load pattern from JSON file"""

        with open(filepath, 'r') as f:
            pattern = json.loads(f.read())

        self.full_pattern = pattern

        self.predefined_variables   = pattern['predefined_variables']
        self.input_directories      = [RegexEntry(v) for v in pattern['input_directories']]
        self.input_files            = {k: RegexEntry(v)   for k, v in pattern['input_files'].items()}  # noqa: E501
        self.parsed_variables       = {k: RegexEntry(v)   for k, v in pattern['parsed_variables'].items()}  # noqa: E501
        self.output_files           = {k: PatternEntry(v) for k, v in pattern['output_files'].items()}  # noqa: E501
        self.technical_requirements = pattern.get('technical_requirements') or None

        if 'required_textures' in pattern:
            self.required_textures = pattern['required_textures']
        else:
            self.required_textures = REQUIRED_TEXTURES

        if compile:
            self.compile()

        return pattern

    @staticmethod
    def fromfile(filepath, compile=True):
        """Constructs an instance by reading a config file"""

        with open(filepath, 'r') as f:
            return TexPatterns(pattern=json.loads(f.read()), compile=compile)

    def __eq__(self, other):
        return (
            self.full_pattern               == other.full_pattern
            and self.input_files            == other.input_files
            and self.output_files           == other.output_files
            and self.required_textures      == other.required_textures
            and self.technical_requirements == other.technical_requirements
            and self.parsed_variables       == self.parsed_variables
        )

    def __ne__(self, other):
        return (
            self.full_pattern              != other.full_pattern
            or self.input_files            != other.input_files
            or self.output_files           != other.output_files
            or self.required_textures      != other.required_textures
            or self.technical_requirements != other.technical_requirements
            or self.parsed_variables       != self.parsed_variables
        )

    def __str__(self):
        return pformat(self.__dict__)
