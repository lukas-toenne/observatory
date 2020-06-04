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
from math import *
import numpy as np
from numpy import fft as fft

margin = 3

"""Convert data array into image pixels."""
def ndarray_to_image(array, image, allow_resize=False):
    assert(len(array.shape) == 2)

    w = array.shape[0]
    h = array.shape[1]
    if allow_resize:
        if image.source != 'GENERATED':
            image.source = 'GENERATED'
        if image.generated_width != w:
            image.generated_width = w
        if image.generated_height != h:
            image.generated_height = h
    else:
        assert(image.source == 'GENERATED')
        assert(image.size[0] == w)
        assert(image.size[1] == h)

    values = (array * 0.5 + 0.5).astype(np.float32)

    imgdata = np.dstack((values, values, values, np.ones(values.shape)))
    image.pixels = imgdata.flatten().tolist()
    image.preview.reload()


def compute_sampling_image(world, antennas):
    if len(antennas) < 2:
        return False
    w = world.interferometry.image_width
    h = world.interferometry.image_height
    if w < 1 or h < 1:
        return False

    Bmax = 0.0
    for i, a in enumerate(antennas):
        for b in antennas[i+1:]:
            B = (b.xy - a.xy).length
            if B > Bmax:
                Bmax = B
    # bounds_min = antennas[0].xy
    # bounds_max = antennas[0].xy
    # for a in antennas[1:]:
    #     if a.x < bounds_min.x:
    #         bounds_min.x = a.x
    #     if a.x > bounds_max.x:
    #         bounds_max.x = a.x
    #     if a.y < bounds_min.y:
    #         bounds_min.y = a.y
    #     if a.y > bounds_max.y:
    #         bounds_max.y = a.y

    epsilon = 1.0e-6
    scale = (0.5 * min(w, h) - margin) / Bmax
    invscale = 1.0/scale if scale > epsilon else 1.0


    # Construct sampling from baselines
    # w2 = w // 2
    # h2 = h // 2
    # sampling = np.zeros((2*w2 + 1, 2*h2 + 1), dtype=np.float32)
    # For real-valued output the input is complex conjugate
    # and irfft expects only the positive components.
    sampling = np.zeros((w + 1, h*2 + 1), dtype=np.float32)
    for i, a in enumerate(antennas):
        for b in antennas[i+1:]:
            B = b.xy - a.xy
            s = B * scale
            # Symmetric sampling in the uv space
            # Ignore value with negative real part
            if s.x >= 0.0:
                sampling[int(0.5 + s.x), int(h/2 + 0.5 + s.y)] = 1.0
            else:
                sampling[int(0.5 + s.x), int(h/2 + 0.5 - s.y)] = 1.0

    # Compute point spread function
    # sampling = fft.ifftshift(sampling)
    pointspread = fft.irfft2(sampling, s=(w, h), norm="ortho")
    # pointspread_r = pointspread[0::1, 0::2]
    print(sampling.shape, pointspread.shape, pointspread.dtype)

    sampling_image = world.interferometry.get_sampling_image(create=True)
    ndarray_to_image(sampling, sampling_image, allow_resize=True)
    pointspread_image = world.interferometry.get_pointspread_image(create=True)
    ndarray_to_image(pointspread * 10.0, pointspread_image, allow_resize=True)

    return True