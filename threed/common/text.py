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


import re

from collections import OrderedDict

def more_readable_regex(regex):
    """
    Takes in regex word and replaces or removes regex symbols so the output
    would be more comprehensible. Intended to be used in cases like user-error
    output text formatting.

    Arguments:
        regex {string} -- regex, usually from Exception output.

    Returns:
        str -- formated word, without all the unnecessary regex jargon.
    """

    regex_dict = OrderedDict(
        (
            (r"(", ""),
            (r")", ""),
            (r"(", ""),
            (r")", ""),
            (r"^", ""),
            (r"$", ""),
            (r"\d?\d?", "(digit(s))"),
            (r"?:", ""),
            (r"{0,}", ""),
            (r"{2}", "+"),
            (r".+", "(alphanumeric(s))"),
            (r".\w+", ""),
            (r"\w+", "(letter(s))"),
            (r"\w", "(letter)"),
            (r"\d+", "(digit(s))"),
            (r"\d", "(digit)"),
        )
    )

    for fr, to in regex_dict.items():
        regex = regex.replace(fr, to)

    return regex
