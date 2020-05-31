# ##### BEGIN MIT LICENSE BLOCK #####
#
# Copyright (c) 2020 Lukas Toenne
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####

# <pep8 compliant>

from mathutils import Vector, Quaternion, Euler, Matrix
import time
from math import pi
import re

def hour_to_angle(hourstr):
    t = time.strptime(hourstr, "%Hh%Mm%Ss")
    return 2.0 * pi * (t.tm_hour + (t.tm_min + t.tm_sec / 60) / 60) / 24

def angle_to_hour(angle):
    frac = (0.5 * angle / pi) % 1.0 if angle >= 0.0 else 1.0 - ((-0.5 * angle / pi) % 1.0)
    h, frac = divmod(frac * 24.0, 1.0)
    m, frac = divmod(frac * 60.0, 1.0)
    s = frac * 60.0
    return "{:d}h{:d}m{:d}s".format(int(h), int(m), int(s))

# hour_expr = re.compile(r"\s*(?Phour\d+)h|H\s*")
hour_expr = re.compile(r"\s*(?P<hours>\d+)h|H\s*(?P<minutes>\d+)m|M\s*(?P<seconds>\d+)s|S\s*")

def parse_hour_angle(hourstr, default):
    m = hour_expr.match(hourstr)
    if m is None:
        print("FAIL: ")
        return default

    print(m.group("hours"), m.group("minutes"), m.group("seconds"))
    return 0.0