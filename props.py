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
from bpy_types import RNAMetaPropGroup
from math import pi
from typing import get_type_hints
from .coordinates import *


# Speed of light
c = 299792458.0


sky_background_items = [
    ('NONE', "None", "No background"),
    ('VISIBLE', "Visible", "Stars in the visible spectrum"),
]


def update_property_group(self, context):
    self.id_data.observatory.update_generic(context)

def MakeGridSettings(def_enabled=False, def_color=(0.8, 0.8, 0.8)):
    class GridSettings(PropertyGroup):
        enabled : BoolProperty(
            name="Show Grid",
            description="Enable background grid display",
            default=def_enabled,
            update=update_property_group,
            )

        color : FloatVectorProperty(
            name="Color",
            description="Enable background grid display",
            subtype='COLOR',
            size=3,
            default=def_color,
            update=update_property_group,
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

ObservatoryLocation = MakeCelestialCoordinate(update=update_property_group)
TargetCoordinate = MakeCelestialCoordinate(default=(0.0, pi/2), update=update_property_group)
HorizontalGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.309342, 0.186442, 0.012358))
EquatorialGridSettings = MakeGridSettings(def_enabled=True, def_color=(0.009179, 0.459465, 0.8))
EclipticGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.004964, 0.137349, 0.002201))
GalacticGridSettings = MakeGridSettings(def_enabled=False, def_color=(0.233609, 0.010037, 0.228179))

def get_nodegroup(create=False):
    nodegroup = bpy.data.node_groups.get("ObservatorySettings")
    if create and nodegroup is None:
        nodegroup = bpy.data.node_groups.new("ObservatorySettings", 'ShaderNodeTree')
    return nodegroup

class ObservatorySettings(bpy.types.PropertyGroup):
    def update_generic(self, context):
        self.update_nodegroup(context)

    location : PointerProperty(type=ObservatoryLocation)

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

    def get_projected_baselines(antennas):
        return []

    def draw(self, context, layout):
        layout.prop(self, "sky_background")

        self.location.draw_long_lat(context, layout)

        self.horizontal_grid.draw(context, layout, "Horizontal Grid")
        self.equatorial_grid.draw(context, layout, "Equatorial Grid")
        self.ecliptic_grid.draw(context, layout, "Ecliptic Grid")
        self.galactic_grid.draw(context, layout, "Galactic Grid")

    def update_nodegroup(self, context):
        nodegroup = get_nodegroup()
        if nodegroup is None:
            return
        node = next((n for n in nodegroup.nodes if n.type=='GROUP_OUTPUT'), None)
        if node is None:
            node = nodegroup.nodes.new("NodeGroupOutput")

        def ensure_output(prop, value, type):
            output = nodegroup.outputs.get(prop)
            if output is None:
                output = nodegroup.outputs.new(type, prop)
            socket = next(s for s in node.inputs if s.identifier==output.identifier)
            socket.default_value = value

        ensure_output("Location Longitude", self.location.longitude, "NodeSocketFloat")
        ensure_output("Location Latitude", self.location.latitude, "NodeSocketFloat")
        ensure_output("Sky Background", self.bl_rna.properties["sky_background"].enum_items[self.sky_background].value, "NodeSocketFloat")

        def ensure_grid_outputs(grid, name):
            ensure_output("{} Enabled".format(name), grid.enabled, "NodeSocketFloat")
            ensure_output("{} Color".format(name), (*grid.color[:3], 1.0), "NodeSocketColor")
        ensure_grid_outputs(self.horizontal_grid, "Horizontal Grid")
        ensure_grid_outputs(self.equatorial_grid, "Equatorial Grid")
        ensure_grid_outputs(self.ecliptic_grid, "Ecliptic Grid")
        ensure_grid_outputs(self.galactic_grid, "Galactic Grid")


sampling_id = "ObservatorySampling"
default_frequency = 1.428e9

class InterferometrySettings(bpy.types.PropertyGroup):
    target : PointerProperty(type=TargetCoordinate)

    frequency : FloatProperty(
        name="Frequency",
        description="Frequency measured by antennas",
        default=default_frequency,
        min=0.0,
        soft_min=10e6,
        soft_max=1e12,
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

    def draw(self, context, layout):
        self.target.draw_long_lat(context, layout, label="Target")

        layout.prop(self, "frequency_mhz", text="Frequency (MHz)")
        layout.prop(self, "wavelength")

        layout.label(text="Image size:")
        row = layout.row(align=True)
        row.prop(self, "image_width", text="")
        row.prop(self, "image_height", text="")

        layout.separator()
        layout.operator("observatory.compute_sampling_image")
        img, data, prop = self.get_image_data_prop(sampling_id)
        if data:
            layout.template_ID_preview(data, prop)

    def get_image_data_prop(self, name, create=False):
        img = bpy.data.images.get(name)
        if create and img is None:
            # img = bpy.data.images.new(name, self.image_width, self.image_height, float_buffer=True, is_data=True)
            img = bpy.data.images.new(name, self.image_width, self.image_height)
            img.use_fake_user = True

        nodegroup = get_nodegroup(create=create)
        data = nodegroup.nodes.get(name)
        if create and data is None:
            data = nodegroup.nodes.new("ShaderNodeTexImage")
            data.name = name
            data.image = img
        return img, data, "image"

    def get_image(self, name, create=False):
        img, data, prop = self.get_image_data_prop(name, create=create)
        return img

    def get_sampling_image(self, create=False):
        return self.get_image(sampling_id, create=create)


def register():
    bpy.utils.register_class(ObservatoryLocation)
    bpy.utils.register_class(TargetCoordinate)
    bpy.utils.register_class(HorizontalGridSettings)
    bpy.utils.register_class(EquatorialGridSettings)
    bpy.utils.register_class(EclipticGridSettings)
    bpy.utils.register_class(GalacticGridSettings)
    bpy.utils.register_class(ObservatorySettings)
    bpy.utils.register_class(InterferometrySettings)

    bpy.types.World.observatory = PointerProperty(type=ObservatorySettings)
    bpy.types.World.interferometry = PointerProperty(type=InterferometrySettings)

def unregister():
    del bpy.types.World.observatory
    del bpy.types.World.interferometry

    bpy.utils.unregister_class(ObservatoryLocation)
    bpy.utils.unregister_class(TargetCoordinate)
    bpy.utils.unregister_class(HorizontalGridSettings)
    bpy.utils.unregister_class(EquatorialGridSettings)
    bpy.utils.unregister_class(EclipticGridSettings)
    bpy.utils.unregister_class(GalacticGridSettings)
    bpy.utils.unregister_class(ObservatorySettings)
    bpy.utils.unregister_class(InterferometrySettings)
