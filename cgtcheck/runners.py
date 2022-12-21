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
This includes check runner classes for easier management of checks.
"""
from __future__ import (division, print_function, absolute_import, unicode_literals)

import logging
import os
import sys
from collections import namedtuple

from cgtcheck.collector import EntityCollector
from cgtcheck.common import Check


logger = logging.getLogger(__name__)


class CheckRunner(object):

    _check_classes = []  # type: list[type[Check]]

    def __init__(self, checks_spec, checks_data=None, dcc=None):
        # type: (dict, dict|None, str|None) -> None
        if dcc is None:
            dcc = self._detect_dcc()
        self.dcc = dcc
        self.checks_spec = checks_spec
        self.checks_data = checks_data

        tex_paths = (checks_data or {}).get('tex_paths', None)
        input_file = (checks_data or {}).get('input_file', None)
        tex_spec = (checks_data or {}).get('tex_spec', None)
        uid = (checks_data or {}).get('uid', None)

        self.collector = self.get_collector(
            dcc=dcc,
            tex_paths=tex_paths,
            input_file=input_file,
            tex_spec=tex_spec,
            uid=uid
        )

        self.checks = [
            cls(
                checks_spec=self.checks_spec,
                checks_data=self.checks_data,
                collector=self.collector
            ) for cls in self._check_classes
        ]  # type: list[Check]
        self.passed = None  # type: bool|None

    @staticmethod
    def _detect_dcc():
        # type: () -> str | None
        """
        Makes an informed guess about which DCC application it's running in.

        Returns:
            'Blender'
            None
        """
        if os.path.basename(sys.argv[0]).lower() in ('blender', 'blender.exe'):
            return 'Blender'
        return None

    @staticmethod
    def get_collector(dcc, tex_paths=None, input_file=None, tex_spec=None, uid=None):
        # type: (str, dict, str, dict, str) -> EntityCollector
        """
        Returns a relevant entity collector for a given dcc.

        Args:
            dcc: either of: 'Blender' or None
            tex_paths: dict with materials and texture paths for each used slot
            input_file: string with path to scene file
            tex_spec: texture specification
            uid: MR uid
        """
        if dcc == 'Blender':
            from cgtcheck.blender.collector import BlenderEntityCollector
            return BlenderEntityCollector(
                tex_paths=tex_paths,
                input_file=input_file,
                tex_spec=tex_spec,
                uid=uid
            )
        elif dcc is None:
            logger_msg = 'No collector found for current DCC. Using "Generic"'
            logger.warning(msg=logger_msg)
            from cgtcheck.generic.collector import GenericEntityCollector
            return GenericEntityCollector(
                tex_paths=tex_paths,
                input_file=input_file,
                tex_spec=tex_spec,
                uid=uid
            )
        else:
            raise NotImplementedError('No collector found for "{}" DCC.'.format(dcc))

    @classmethod
    def import_dcc_checks(cls, dcc=None):
        # type: (str) -> None
        """
        Imports all checks from modules relevant to current DCC application.
        Note: FBX SDK not currently handled as a DCC application.

        Args:
            dcc: if supplied should be 'Blender'
        """
        if dcc is None:
            dcc = cls._detect_dcc()

        import cgtcheck.generic.all_checks  # noqa F401
        if dcc == 'Blender':
            import cgtcheck.blender.all_checks  # noqa F401

    def update(self, checks_spec=None, checks_data=None):
        # type: (dict, dict) -> None
        """
        Updates configuration data stored in runner and all its checks.
        """

        if checks_spec:
            self.checks_spec.update(checks_spec)

        if checks_data:
            self.checks_data.update(checks_data)

    def blacklist_checks(self, keys):
        """
        Disable checks with given keys
        """
        for check in self.checks:
            if check.key in keys:
                check.params['enabled'] = False

    def whitelist_checks(self, keys):
        """
        Enable checks with given keys
        """
        for check in self.checks:
            if check.key in keys:
                check.params['enabled'] = True

    def isolate_checks(self, keys):
        """
        Isolate checks with given keys (disable rest of checks)
        """
        for check in self.checks:
            if check.key in keys:
                check.params['enabled'] = True
            else:
                check.params['enabled'] = False

    def runall(self):
        # type: () -> bool
        """
        Runs all checks and returns True if all pass, or False if any fail.
        Updates self.passed value in addition.
        """
        self.collector.collect()

        for chk in self.checks:
            if chk.is_enabled():
                chk.run()

        self.passed = all(chk.passed for chk in self.checks)
        return self.passed

    def run_all_report_per_check(self, selection_only=False):
        # type: (bool) -> None
        """
        Runs all enabled checks and yields report per every executed check.

        Report is generated regardless of check's report_type value.
        In addition updates self.passed value to False if any run check fails, True otherwise
            (e.g. no check executed, all checks pass).
        """
        self.collector.collect(selection_only)

        for chk in self.checks:
            if chk.is_enabled():
                chk.run()
                report = chk.format_report()
                report['passed'] = chk.passed
                yield report

        self.passed = all(chk.passed for chk in self.checks)

    def reset(self):
        self.passed = None
        for chk in self.checks:
            chk.reset()

    @classmethod
    def register(cls, check_cls):
        # type: (object) -> object
        """
        Adds check to be tracked by CheckRunner class.
        Does not modify check in any way.
        """
        cls._check_classes.append(check_cls)
        return check_cls

    def has_errors(self):
        # type: () -> bool
        """
        Returns True if any checks were failed with an error
        """
        return any(
            chk.passed is False for chk in self.checks
            if chk.report_type == 'error'
        )

    def error_messages(self):
        # type: () -> list[str]
        return [
            chk.fail_message() for chk in self.checks
            if (not chk.passed) and chk.report_type == 'error'
        ]

    def error_message(self):
        # type: () -> str
        return "\n".join(self.error_messages())

    def warning_messages(self):
        # type: () -> list[str]
        return [
            chk.fail_message() for chk in self.checks
            if (not chk.passed) and chk.report_type == 'warning'
        ]

    def warning_message(self):
        # type: () -> str
        return "\n".join(self.warning_messages())

    def format_reports(self, msg_type=None):
        # type: (str|None) -> list[dict]
        """
        Format report structures for current failures.
        Note that it does not include details.

        Args:
            msg_type: type of failures to format: 'warning'/'error', will include both if None
        """
        return [
            chk.format_report() for chk in self.checks
            if not chk.passed and chk.is_enabled()
            and chk.report_type != 'details' and msg_type in (None, chk.report_type)
        ]

    def format_details(self):
        # type: () -> dict
        """
        Return checks results details dictionary to be reported to wildcat.
        Details of all checks are merged together into a single dict,
        and stored under checks_results key.
        """
        checks = (
            chk.format_details() for chk in self.checks
            if chk.report_type == 'details' and chk.is_enabled()
        )
        check_details = list(filter(None, checks))
        details = {}
        if not check_details:
            return details
        for d in check_details:
            if d is not None:
                details.update(d)
        return {'checks_results': details}

    def format_properties(self):
        # type: () -> dict
        """
        Return scene entities' properties, checks' reports and their versions.
        All information is combined into one dict, which is intended to be reported.
        """
        objs = [{'name': obj.name} for obj in self.collector.objects]
        materials = [{'name': mtl.name} for mtl in self.collector.materials]

        CheckProps = namedtuple('CheckData', 'check properties')  # type: tuple[Check, dict]
        checks_properties = (
            CheckProps(chk, chk.format_properties()) for chk in self.checks if chk.is_enabled()
        )
        checks_properties = [item for item in checks_properties if item.properties is not None]  # type: list[CheckProps]  # noqa E501

        properties_report = {
            'entities': {
                'objects': objs,
                'materials': materials
            },
            'checks': {
                check.key: {
                    'version': check.version,
                    'details': properties,
                }
                for check, properties in checks_properties
            },
        }
        return properties_report

    def get_versions(self):
        # type: () -> dict[type[Check], tuple[int, int, int]]
        """
        Returns dict of check version (value) for every check class (key).
        """
        return {chk: chk.version for chk in self._check_classes}

    def __iter__(self):
        return iter(self._check_classes)
