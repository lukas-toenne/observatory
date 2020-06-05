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
from bpy.app.handlers import persistent


def get_nodegroup(create=False):
    nodegroup = bpy.data.node_groups.get("ObservatorySettings")
    if create and nodegroup is None:
        nodegroup = bpy.data.node_groups.new("ObservatorySettings", 'ShaderNodeTree')
    return nodegroup

def update_nodegroup(world, context):
    observatory = world.observatory
    interferometry = world.interferometry

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
        socket = next((s for s in node.inputs if s.identifier==output.identifier))
        socket.default_value = value

    ensure_output("Location Longitude", observatory.location.longitude, "NodeSocketFloat")
    ensure_output("Location Latitude", observatory.location.latitude, "NodeSocketFloat")
    ensure_output("Sky Background", observatory.bl_rna.properties["sky_background"].enum_items[observatory.sky_background].value, "NodeSocketFloat")

    def ensure_grid_outputs(grid, name):
        ensure_output("{} Enabled".format(name), grid.enabled, "NodeSocketFloat")
        ensure_output("{} Color".format(name), (*grid.color[:3], 1.0), "NodeSocketColor")
    ensure_grid_outputs(observatory.horizontal_grid, "Horizontal Grid")
    ensure_grid_outputs(observatory.equatorial_grid, "Equatorial Grid")
    ensure_grid_outputs(observatory.ecliptic_grid, "Ecliptic Grid")
    ensure_grid_outputs(observatory.galactic_grid, "Galactic Grid")


def get_image_data_prop(name, create=False, width=128, height=128):
    img = bpy.data.images.get(name)
    if create and img is None:
        img = bpy.data.images.new(name, width, height)
        img.use_fake_user = True

    nodegroup = get_nodegroup(create=create)
    data = nodegroup.nodes.get(name)
    if create and data is None:
        data = nodegroup.nodes.new("ShaderNodeTexImage")
        data.name = name
        data.image = img
    return img, data, "image"


def get_antenna_collection():
    return bpy.data.collections.get("Observatory")
