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

from bpy.props import FloatProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from mathutils import Vector, Quaternion, Euler, Matrix
import time
from math import *
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

def MakeCelestialCoordinate(default=(0.0, 0.0), update=None):
    class CelestialCoordinateProp(PropertyGroup):
        co : FloatVectorProperty(
            name="Coordinate",
            description="Coordinate in angles east and north",
            size=2,
            subtype='EULER',
            unit='ROTATION',
            default=default,
            update=update,
            )

        def _get_longitude(self):
            return self.co[0]
        def _set_longitude(self, value):
            self.co[0] = value
        longitude : FloatProperty(
            name="Longitude",
            description="Longitude angle",
            subtype='ANGLE',
            unit='ROTATION',
            default=default[0],
            soft_min=-pi,
            soft_max=pi,
            get=_get_longitude,
            set=_set_longitude,
            )

        def _get_hour(self):
            return self.co[0] * 12.0 / pi
        def _set_hour(self, value):
            self.co[0] = value * pi / 12.0
        hour : FloatProperty(
            name="Hour",
            description="Longitude as hour angle",
            subtype='TIME',
            unit='TIME',
            default=default[0] * 12.0 / pi,
            soft_min=-12.0,
            soft_max=12.0,
            get=_get_hour,
            set=_set_hour,
            )

        def _get_latitude(self):
            return self.co[1]
        def _set_latitude(self, value):
            self.co[1] = value
        latitude : FloatProperty(
            name="Latitude",
            description="Latitude angle",
            subtype='ANGLE',
            unit='ROTATION',
            default=default[1],
            soft_min=-pi/2,
            soft_max=pi/2,
            get=_get_latitude,
            set=_set_latitude,
            )

        def draw_long_lat(self, context, layout, label=None):
            row = layout.row(align=True)
            if label:
                row.label(text=label)
            row.prop(self, "longitude")
            row.prop(self, "latitude")

        def draw_hour_lat(self, context, layout, label=None):
            row = layout.row(align=True)
            if label:
                row.label(text=label)
            row.prop(self, "hour")
            row.prop(self, "latitude")

    return CelestialCoordinateProp

def horizontal_to_equatorial(co, observer_latitude):
    A = co[0]
    a = co[1]
    h = atan2(sin(A), cos(A)*sin(observer_latitude) + tan(a)*cos(observer_latitude))
    delta = asin(sin(a)*sin(observer_latitude) - cos(a)*cos(A)*cos(observer_latitude))
    return (h, delta)

def equatorial_to_horizontal(co, observer_latitude):
    h = co[0]
    delta = co[1]
    A = atan2(sin(h), cos(h)*sin(observer_latitude) - tan(delta)*cos(observer_latitude))
    a = asin(sin(delta)*sin(observer_latitude) + cos(delta)*cos(h)*cos(observer_latitude))
    return (A, a)
