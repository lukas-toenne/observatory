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


class DownloadSkyMapTexturesOperator(bpy.types.Operator):
    """Download textures for the sky map"""
    bl_idname = "observatory.download_skymap_textures"
    bl_label = "Download Sky Map Textures"

    @classmethod
    def poll(cls, context):
        image = bpy.data.images.get("SkyMap.tif")
        if image is None:
            return False
        if image.source != 'FILE':
            return False
        return not image.has_data

    def execute(self, context):
        import os.path
        import urllib.request

        world = context.world
        if world.library is None:
            dirpath = bpy.path.abspath("//blendfiles/SkyMap/SkyMap.tif")
        else:
            dirpath = os.path.dirname(bpy.path.abspath(world.library.filepath))
        filepath = os.path.join(dirpath, "SkyMap.tif")
        print("File path: ", filepath)

        url = 'https://svs.gsfc.nasa.gov/vis/a000000/a003500/a003572/TychoSkymapII.t3_04096x02048.tif'
        urllib.request.urlretrieve(url, filepath)

        image = bpy.data.images.get("SkyMap.tif")
        image.reload()
        image.update()
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

        if not sampling.compute_sampling_image(world, antennas):
            return {'CANCELLED'}

        sampling.execute_all_image_pixel_updates(world)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(AddObservatorySettingsNodeGroupOperator)
    bpy.utils.register_class(DownloadSkyMapTexturesOperator)
    bpy.utils.register_class(ComputeSamplingImageOperator)

def unregister():
    bpy.utils.unregister_class(AddObservatorySettingsNodeGroupOperator)
    bpy.utils.unregister_class(DownloadSkyMapTexturesOperator)
    bpy.utils.unregister_class(ComputeSamplingImageOperator)
