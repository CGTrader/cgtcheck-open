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

import sys
from pathlib import Path

import cgtcheck
from cgtcheck.blender import all_checks  # noqa F401 # This is necessary for checks to be registered

sys.path.insert(0, str(Path(__file__).parent))

enabled_checks = {
    'triangleMaxCount': {
        'enabled': True,
        'type': 'error',
        'parameters': {
            'triMaxCount': 1
        }
    }
}

runner = cgtcheck.runners.CheckRunner(
    checks_spec=enabled_checks, checks_data={}
)
runner.runall()
reports = runner.format_reports()
print(reports)
