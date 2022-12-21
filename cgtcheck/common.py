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
Contains common checks functionality and utility functions
"""

from copy import deepcopy
from abc import ABCMeta, abstractmethod

import cgtcheck.metadata
import cgtcheck.collector


class Check(object):

    key = None  # type: str  # subclass should define a key
    version = (0, 0, 0)  # type: tuple[int, int, int]  # subclass should override

    def __init__(self, checks_spec=None, checks_data=None, collector=None):
        # type: (dict, dict|None, cgtcheck.collector.EntityCollector|None) -> None
        self.metadata = cgtcheck.metadata.checks[self.key]  # please register a new check there
        self.failures = []  # type: list|dict
        self.properties = []  # type: list|dict
        self.params = deepcopy(self.metadata.params)
        if checks_spec is not None:
            self.params.update(checks_spec.get(self.key, {}))
        self.report_type = self.params.get('type', 'warning')  # type: str
        self.checks_data = checks_data
        self.collector = collector

    @property
    def passed(self):
        return not bool(self.failures)

    def final_params(self):
        # type: () -> dict
        """
        Returns a dictionary merging default parameters with supplied ones
        """
        merged = deepcopy(self.metadata.params)
        merged.update(self.params)
        return merged

    def run(self):
        """
        Perform the associated check.
        """
        raise NotImplementedError('The run() method of check needs to be overriden')

    def reset(self):
        # type: () -> None
        """
        Resets check state so that its ready to be run again.
        """
        # both failures and properties should be either list or dict, but python2 list has no clear
        if hasattr(self.properties, 'clear'):
            self.properties.clear()
        else:
            del self.properties[:]

        if hasattr(self.failures, 'clear'):
            self.failures.clear()
        else:
            del self.failures[:]

    def is_enabled(self):
        # type: () -> bool
        return self.params.get('enabled', False)

    def get_failures(self):
        # type () -> list[object]
        """
        Return an iterable of failures.
        In subclassed code, iterable may be a generator, not necessarily a list
        """
        return self.failures

    def list_failures(self):
        # type () -> list[str]
        """
        Returns list of found issues for this check
        """
        return [str(f) for f in self.failures]

    def fail_message(self, indent='  '):
        # type (indent=str) -> str
        """
        Returns failure message to display.
        If a check has failures, they are appended indented.
        """
        msg = u'{}'.format(self.metadata.msg)
        failures = self.list_failures()
        if failures:
            msg += u':\n' + indent + (u'\n' + indent).join(failures)
        return msg

    def format_failure(self, failure):
        # type: (str|object) -> dict[str, str|int|float]
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        This is intended to be overriden to something more useful per-check.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
            'expected': None,
            'found': None,
        }

    def format_report(self):
        # type: () -> dict[str, object]
        """
        Makes a dictionary for reporting error/warning to Wildcat with additional metadata.
        Note: does not include the legacy "warning"/"error" keys.

        Return:
            dict - formatted report dictionary
        """
        return {
            'message': self.metadata.msg,
            'identifier': self.key,
            'msg_type': self.report_type,
            'items': [self.format_failure(failure) for failure in self.get_failures()]
        }

    def format_details(self):
        # type: () -> dict[str, str|bool]|None
        """
        Format a details report to be sent to Wildcat. Relevant to some checks.
        None should be returned if the check does not implement details, or is not enabled to be
        reported as details.
        """
        return None

    def get_description(self):
        # type: () -> str
        """
        Return check description for check.
        """
        if self.metadata.check_description:
            return self.metadata.check_description
        return ''


# to ensure compatiblity with Python 2 and 3
ABC = ABCMeta(str('ABC'), (object,), {'__slots__': ()})


class Properties(ABC):
    @abstractmethod
    def format_properties(self):
        # type: () -> None
        """
        Abstract method for formating properties, has to be overriden in child classes.
        """
        pass

    def _basic_format_properties(self):
        # type: () -> dict[str, list[dict]]
        """
        Basic implementation of format_properties can be used to override abstract in child classes.
        """
        return {
            'objects': self.properties
        }
