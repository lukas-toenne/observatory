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


sky_background_items = [
    ('NONE', "None", "No background"),
    ('VISIBLE', "Visible", "Stars in the visible spectrum"),
]


def MakeGridSettings(enable=False, def_color=(0.8, 0.8, 0.8)):
    class GridSettings(PropertyGroup):
        show_grid : BoolProperty(
            name="Show Grid",
            description="Enable background grid display",
            default=enable,
            )

        color : FloatVectorProperty(
            name="Color",
            description="Enable background grid display",
            subtype='COLOR',
            size=3,
            default=def_color,
            )

        def draw(self, context, layout, label):
            col = layout.box()

            row = col.row(align=True)
            row.prop(self, "show_grid", text="")
            row.label(text=label)

            col2 = col.column(align=True)
            col2.enabled = self.show_grid
            col2.prop(self, "color")

    return GridSettings

HorizontalGridSettings = MakeGridSettings(enable=False, def_color=(0.309342, 0.186442, 0.012358))
EquatorialGridSettings = MakeGridSettings(enable=True, def_color=(0.009179, 0.459465, 0.8))
EclipticGridSettings = MakeGridSettings(enable=False, def_color=(0.004964, 0.137349, 0.002201))
GalacticGridSettings = MakeGridSettings(enable=False, def_color=(0.233609, 0.010037, 0.228179))


def get_nodegroup(create=False):
    nodegroup = bpy.data.node_groups.get("ObservatorySettings")
    if create and nodegroup is None:
        nodegroup = bpy.data.node_groups.new("ObservatorySettings", 'ShaderNodeTree')
    return nodegroup

class ObservatorySettings(bpy.types.PropertyGroup):
    def update_generic(self, context):
        self.update_nodegroup(context)

    sky_background : EnumProperty(
        name="Sky Background",
        description="Sky background type to render",
        items=sky_background_items,
        default='NONE',
        update=update_generic,
        )

    longitude : FloatProperty(
        name="Longitude",
        description="Observatory location longitude",
        subtype='ANGLE',
        unit='ROTATION',
        soft_min=0,
        soft_max=2.0*pi,
        update=update_generic,
        )

    latitude : FloatProperty(
        name="Latitude",
        description="Observatory location latitude",
        subtype='ANGLE',
        unit='ROTATION',
        soft_min=-0.5*pi,
        soft_max=0.5*pi,
        update=update_generic,
        )

    def get_longitude_string(self):
        return angle_to_hour(self.longitude)
    def set_longitude_string(self, value):
        self.longitude = parse_hour_angle(value, self.longitude)
    longitude_string : StringProperty(
        name="Longitude",
        description="Observatory location longitude",
        options={'SKIP_SAVE'},
        get=get_longitude_string,
        set=set_longitude_string,
        )

    horizontal_grid : PointerProperty(type=HorizontalGridSettings)
    equatorial_grid : PointerProperty(type=EquatorialGridSettings)
    ecliptic_grid : PointerProperty(type=EclipticGridSettings)
    galactic_grid : PointerProperty(type=GalacticGridSettings)

    def draw(self, context, layout):
        layout.prop(self, "sky_background")

        row = layout.row(align=True)
        # row.prop(self, "longitude_string")
        row.prop(self, "longitude")
        row.prop(self, "latitude")

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
        
        ensure_output("longitude", self.longitude, "NodeSocketFloat")
        ensure_output("latitude", self.latitude, "NodeSocketFloat")
        ensure_output("sky_background", self.bl_rna.properties["sky_background"].enum_items[self.sky_background].value, "NodeSocketFloat")


sampling_id = "ObservatorySampling"

class InterferometrySettings(bpy.types.PropertyGroup):
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

    bpy.utils.unregister_class(HorizontalGridSettings)
    bpy.utils.unregister_class(EquatorialGridSettings)
    bpy.utils.unregister_class(EclipticGridSettings)
    bpy.utils.unregister_class(GalacticGridSettings)
    bpy.utils.unregister_class(ObservatorySettings)
    bpy.utils.unregister_class(InterferometrySettings)
