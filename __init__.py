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

bl_info = {
    'name': 'Observatory',
    'author': 'Lukas Toenne',
    'version': (1, 0, 0),
    'blender': (2, 82, 0),
    'location': '3D View',
    'description':
        'Radio interferometry simulation',
    "wiki_url": "",
    'category': 'Add Mesh',
    'support': 'COMMUNITY',
}

# Runtime script reload
if "bpy" in locals():
    import importlib

    from . import coordinates, convolution, operator, props, sampling, ui
    importlib.reload(coordinates)
    importlib.reload(convolution)
    importlib.reload(props)
    importlib.reload(operator)
    importlib.reload(sampling)
    importlib.reload(ui)

import bpy
from . import operator, props, ui


def register():
    operator.register()
    props.register()
    ui.register()


def unregister():
    operator.unregister()
    props.unregister()
    ui.unregister()


if __name__ == '__main__':
    register()
