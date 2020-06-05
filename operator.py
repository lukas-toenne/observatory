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
from bpy_types import Operator
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty
from . import sampling, data_links


class AddObservatorySettingsNodeGroupOperator(bpy.types.Operator):
    """Create a node group for exposing observatory settings in shaders"""
    bl_idname = "observatory.add_settings_node_group"
    bl_label = "Add Observatory Settings Node Group"

    def execute(self, context):
        nodegroup = context.world.observatory.get_nodegroup(create=True)
        return {'FINISHED'}


class ComputeSamplingImageOperator(bpy.types.Operator):
    """Compute the sampling image based on antenna configuration"""
    bl_idname = "observatory.compute_sampling_image"
    bl_label = "Compute Sampling Image"

    def execute(self, context):
        world = context.world

        antennas = data_links.find_antennas(context, op=self)
        if antennas is None:
            return {'CANCELLED'}

        if sampling.compute_sampling_image(world, antennas):
            return {'FINISHED'}

        return {'CANCELLED'}


def register():
    bpy.utils.register_class(AddObservatorySettingsNodeGroupOperator)
    bpy.utils.register_class(ComputeSamplingImageOperator)

def unregister():
    bpy.utils.unregister_class(AddObservatorySettingsNodeGroupOperator)
    bpy.utils.unregister_class(ComputeSamplingImageOperator)
