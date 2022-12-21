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
Wrapper for launching tests in Blender.
Pytest must be installed in Blender.
"cgtcheck/cgtcheck/blender/tests" must be set as a current directory.

Run tests in Blender using:
blender --python-use-system-env -b -P launcher_blender.py

Parameters are given to tests after a `--` sentry argument:
blender --python-use-system-env -b -P launcher_blender.py -- -d

Run both Blender & Generic tests:
blender --python-use-system-env -b -P launcher_blender.py -- -ta ../../blender ../../generic
"""

import sys
import os
import logging
import pkgutil
import argparse
from pathlib import Path
from typing import List

import pytest

logger = logging.getLogger(__name__)
# Retrieve topmost dir named "cgtcheck".
PROJECT_DIR = [p for p in Path(__file__).parents if p.name == 'cgtcheck'][-1]
PKG_NAME = os.path.basename(PROJECT_DIR)
BASE_DIR = PROJECT_DIR.parent
DEBUG_PORT = 5677


def parse_args(args: List[str]):
    """
    Args:
        args: argument list to parse, such as sys.argv
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help=f'Wait for debugger attach (port: {DEBUG_PORT}) before running'
    )
    parser.add_argument(
        '-ta', '--test-arguments', dest='test_args', nargs=argparse.REMAINDER, default=[],
        help='Arguments for Pytest'
    )

    return parser.parse_args(args)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s - %(name)s: %(message)s', level=logging.INFO)

    if '--' in sys.argv:
        arguments = sys.argv[sys.argv.index('--') + 1:]
    else:
        arguments = []

    args_parsed = parse_args(arguments)

    if args_parsed.debug:
        import ptvsd
        attach_info = ptvsd.enable_attach(('localhost', DEBUG_PORT))
        logger.warning(f'Waiting for debugger attach at: {attach_info}')
        ptvsd.wait_for_attach()
        ptvsd.break_into_debugger()

    # Prioritize our development locations
    sys.path.insert(0, str(BASE_DIR))

    pkg_load = pkgutil.find_loader(PKG_NAME)
    if pkg_load:
        logger.info(f'{PKG_NAME} is at: {pkg_load.path}')
    else:
        logger.warning(f'{PKG_NAME} location is unknown!')

    test_args = list(args_parsed.test_args)
    test_args.append('-v')
    logger.info(u'Project Dir: {}'.format(PROJECT_DIR))
    sys.exit(pytest.main(test_args))
