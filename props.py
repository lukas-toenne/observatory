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

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup
from bpy.app.handlers import persistent
from math import *
from mathutils import Euler, Quaternion, Vector, Matrix
import time
from .coordinates import MakeCelestialCoordinate, horizontal_to_equatorial, equatorial_to_horizontal
from . import data_links, sampling
from functools import partial


# Speed of light
c = 299792458.0

# Length of sidereal day
solar_to_sidereal = 366.24/365.24
sidereal_to_solar = 365.24/366.24


sky_background_items = [
    ('NONE', "None", "No background"),
    ('VISIBLE', "Visible", "Stars in the visible spectrum"),
]


def update_generic(data, context):
    data_links.update_nodegroup(data.id_data, context)

def MakeGridSettings(def_enabled=False, def_color=(0.8, 0.8, 0.8)):
    class GridSettings(PropertyGroup):
        enabled : BoolProperty(
            name="Show Grid",
            description="Enable background grid display",
            default=def_enabled,
            update=update_generic,
            )

        color : FloatVectorProperty(
            name="Color",
            description="Enable background grid display",
            subtype='COLOR',
            size=3,
            default=def_color,
            update=update_generic,
            )

        def draw(self, context, layout, label):
            col = layout.box()

            row = col.row(align=True)
            row.prop(self, "enabled", text="")
            row.label(text=label)

            col2 = col.column(align=True)
            col2.enabled = self.enabled
            col2.prop(self, "color")

    return GridSettings

class TimeProp(PropertyGroup):
    day : IntProperty(
        name="Day",
        description="Day since the J2000 epoch",
        default=7305,
        update=update_generic,
        )

    hour : FloatProperty(
        name="Hour",
        description="Hour of the day",
        default=12.0,
        min=0.0,
        max=24.0,
        update=update_generic,
        )

    def get_earth_rotation(self):
        f = modf((self.day + self.hour / 24.0) * solar_to_sidereal)[0]
        return f * 2*pi if f > 0.0 else (1.0 - f) * 2*pi
    earth_rotation : FloatProperty(
        name="Earth Rotation Angle",
        description="Earth rotation angle relative to fixed star background since epoch",
        default=pi,
        min=0.0,
        max=pi*2,
        get=get_earth_rotation,
        )

    # TODO add time conversions to python time, Gregorian calender dates, etc.

    def draw(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "day")
        col.prop(self, "hour")

ObservatoryLocation = MakeCelestialCoordinate(update=update_generic)
TargetCoordinate = MakeCelestialCoordinate(default=(0.0, pi/2), update=update_generic)
HorizontalGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.309342, 0.186442, 0.012358))
EquatorialGridSettings = MakeGridSettings(def_enabled=True, def_color=(0.009179, 0.459465, 0.8))
EclipticGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.004964, 0.137349, 0.002201))
GalacticGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.233609, 0.010037, 0.228179))

class ObservatorySettings(bpy.types.PropertyGroup):
    location : PointerProperty(type=ObservatoryLocation)

    def get_equatorial_rotation(self):
        return Euler((self.location.co[1], -self.location.co[0] - self.time.earth_rotation, 0), 'ZYX').to_quaternion()
    equatorial_rotation : FloatVectorProperty(
        name="Equatorial Rotation",
        description="Rotation of the equatorial reference frame to world space",
        size=4,
        subtype='QUATERNION',
        get=get_equatorial_rotation,
        )

    time : PointerProperty(type=TimeProp)

    sky_background : EnumProperty(
        name="Sky Background",
        description="Sky background type to render",
        items=sky_background_items,
        default='NONE',
        update=update_generic,
        )

    horizontal_grid : PointerProperty(type=HorizontalGridSettings)
    equatorial_grid : PointerProperty(type=EquatorialGridSettings)
    ecliptic_grid : PointerProperty(type=EclipticGridSettings)
    galactic_grid : PointerProperty(type=GalacticGridSettings)

    def draw(self, context, layout):
        layout.prop(self, "sky_background")
        if bpy.ops.observatory.download_skymap_textures.poll():
            layout.operator("observatory.download_skymap_textures")

        self.location.draw_long_lat(context, layout)
        self.time.draw(context, layout)

        self.horizontal_grid.draw(context, layout, "Horizontal Grid")
        self.equatorial_grid.draw(context, layout, "Equatorial Grid")
        self.ecliptic_grid.draw(context, layout, "Ecliptic Grid")
        self.galactic_grid.draw(context, layout, "Galactic Grid")


sampling_id = "ObservatorySampling"
pointspread_id = "PointSpread"
trueimage_id = "TrueImage"
dirtybeam_id = "DirtyBeam"
cleanbeam_id = "CleanBeam"
all_image_ids = [sampling_id, pointspread_id, trueimage_id, dirtybeam_id, cleanbeam_id]
default_frequency = 1.428e9

"""
Timer callback for automatically computing images.
"""
def update_images_timer(scene):
    if not scene.interferometry.auto_generate_images:
        # Unregister the timer function
        return None
    sampling.execute_all_image_pixel_updates(scene)
    return scene.interferometry.auto_generate_images_interval

class InterferometrySettings(bpy.types.PropertyGroup):
    @property
    def observatory(self):
        return self.id_data.observatory

    target : PointerProperty(type=TargetCoordinate)
    def get_target_rotation(self):
        return self.observatory.equatorial_rotation @ Euler((self.target.co[1], -self.target.co[0], 0), 'XYZ').to_quaternion()
    target_rotation : FloatVectorProperty(
        name="Target Rotation",
        description="Target rotation in horizonal coordinates",
        size=4,
        subtype='QUATERNION',
        get=get_target_rotation,
        )

    frequency : FloatProperty(
        name="Frequency",
        description="Frequency measured by antennas",
        default=default_frequency,
        min=0.0,
        soft_min=10e6,
        soft_max=1e12,
        update=update_generic,
        )

    def get_frequency_mhz(self):
        return self.frequency * 1.0e-6
    def set_frequency_mhz(self, value):
        self.frequency = value * 1.0e6
    frequency_mhz : FloatProperty(
        name="Frequency",
        description="Frequency measured by antennas in MHz",
        default=default_frequency * 1.0e-6,
        get=get_frequency_mhz,
        set=set_frequency_mhz,
        )

    def get_wavelength(self):
        return c / self.frequency
    def set_wavelength(self, value):
        self.frequency = c / value
    wavelength : FloatProperty(
        name="Wavelength",
        description="Wavelength measured by antennas",
        default=c / default_frequency,
        unit='LENGTH',
        get=get_wavelength,
        set=set_wavelength,
        )

    image_width : IntProperty(
        name="Image Width",
        description="Width of brightness and visibility images",
        min=1,
        soft_max=1024,
        default=128,
        )

    image_height : IntProperty(
        name="Image Height",
        description="Height of brightness and visibility images",
        min=1,
        soft_max=1024,
        default=128,
        )

    def contains_image_dependency(self, updates):
        antennas = data_links.get_antenna_collection()
        objects = set(antennas.objects)
        for u in updates:
            # XXX Workaround for Blender crash:
            # If an object is deleted the 'original' property access will crash.
            # Check if the object still exists in the db.
            if isinstance(u.id, bpy.types.Object) and u.id.name not in bpy.data.objects:
                continue
            if isinstance(u.id, bpy.types.Collection) and u.id.name not in bpy.data.collections:
                continue

            id_data = u.id.original
            if id_data is antennas:
                return True
            if isinstance(id_data, bpy.types.Object):
                if id_data in objects:
                    return True
        return False

    def generate_images(self):
        antennas = data_links.find_antennas(bpy.context)
        if antennas is None:
            return
        sampling.compute_sampling_image(self.id_data, antennas)

    def auto_generate_images_update(self, context):
        if self.auto_generate_images:
            # Note: The function unregisters itself by returning None when auto_generate_images is set False.
            # Storing a reference to the function for explicit unregistering is not reliable within bpy objects.
            bpy.app.timers.register(partial(update_images_timer, scene=self.id_data))

    auto_generate_images : BoolProperty(
        name="Use Auto Update",
        description="Automatically update images when the scene changes",
        default=False,
        update=auto_generate_images_update,
        )

    auto_generate_images_interval : FloatProperty(
        name="Auto Update Interval",
        description="Interval for automatic image updates",
        default=1.0,
        min=0.0,
        soft_min=0.1,
        soft_max=5.0,
        update=auto_generate_images_update,
        )

    def draw(self, context, layout):
        self.target.draw_long_lat(context, layout, label="Target")

        layout.separator()

        row = layout.row(align=True)
        row.prop(self, "frequency_mhz", text="Frequency (MHz)")
        row.prop(self, "wavelength")

        layout.label(text="Image size:")
        row = layout.row(align=True)
        row.prop(self, "image_width", text="")
        row.prop(self, "image_height", text="")

        row = layout.row(align=True)
        row.prop(self, "auto_generate_images", text="Auto Update")
        row2 = row.row(align=True)
        row2.enabled = self.auto_generate_images
        row2.prop(self, "auto_generate_images_interval", text="Interval")

        layout.separator()
        layout.operator("observatory.compute_sampling_image")

        for image_id in all_image_ids:
            img, data, prop = data_links.get_image_data_prop(image_id)
            if data:
                layout.template_ID_preview(data, prop)

    def get_image(self, name, create=False):
        img, data, prop = data_links.get_image_data_prop(name, create=create, width=self.image_width, height=self.image_height)
        return img

    def get_sampling_image(self, create=False):
        return self.get_image(sampling_id, create=create)

    def get_pointspread_image(self, create=False):
        return self.get_image(pointspread_id, create=create)

    def get_trueimage_image(self, create=False):
        return self.get_image(trueimage_id, create=create)

    def get_dirtybeam_image(self, create=False):
        return self.get_image(dirtybeam_id, create=create)

    def get_cleanbeam_image(self, create=False):
        return self.get_image(cleanbeam_id, create=create)


@persistent
def load_handler(scene):
    # Restart timers where needed
    for scene in bpy.data.scenes:
        scene.interferometry.auto_generate_images_update(bpy.context)

@persistent
def depsgraph_handler_pre(scene):
    if scene.interferometry.auto_generate_images:
        # Warning: cannot use the evaluated depsgraph from context, this causes infinite loops!
        depsgraph = bpy.context.window.view_layer.depsgraph
        scene.interferometry["images_updated"] = scene.interferometry.contains_image_dependency(depsgraph.updates)

@persistent
def depsgraph_handler_post(scene):
    if scene.interferometry.auto_generate_images:
        if scene.interferometry.get("images_updated", False):
            scene.interferometry.generate_images()

def register():
    bpy.utils.register_class(ObservatoryLocation)
    bpy.utils.register_class(TargetCoordinate)
    bpy.utils.register_class(TimeProp)
    bpy.utils.register_class(HorizontalGridSettings)
    bpy.utils.register_class(EquatorialGridSettings)
    bpy.utils.register_class(EclipticGridSettings)
    bpy.utils.register_class(GalacticGridSettings)
    bpy.utils.register_class(ObservatorySettings)
    bpy.utils.register_class(InterferometrySettings)

    bpy.types.Scene.observatory = PointerProperty(type=ObservatorySettings)
    bpy.types.Scene.interferometry = PointerProperty(type=InterferometrySettings)

    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.depsgraph_update_pre.append(depsgraph_handler_pre)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler_post)

def unregister():
    del bpy.types.Scene.observatory
    del bpy.types.Scene.interferometry

    bpy.utils.unregister_class(ObservatoryLocation)
    bpy.utils.unregister_class(TargetCoordinate)
    bpy.utils.unregister_class(TimeProp)
    bpy.utils.unregister_class(HorizontalGridSettings)
    bpy.utils.unregister_class(EquatorialGridSettings)
    bpy.utils.unregister_class(EclipticGridSettings)
    bpy.utils.unregister_class(GalacticGridSettings)
    bpy.utils.unregister_class(ObservatorySettings)
    bpy.utils.unregister_class(InterferometrySettings)

    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.depsgraph_update_pre.remove(depsgraph_handler_pre)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler_post)
