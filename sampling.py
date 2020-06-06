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
import queue

# Queues for updated image pixel data
sampling_queue = queue.Queue(maxsize=1)
pointspread_queue = queue.Queue(maxsize=1)

margin = 3

"""
Write pixel data into image data block.
WARNING: This should only be done on the main thread using the sampling queue!
"""
def update_image_pixels(image, pixels, width, height, allow_resize=False):
    if allow_resize:
        if image.source != 'GENERATED':
            image.source = 'GENERATED'
        if image.generated_width != width:
            image.generated_width = width
        if image.generated_height != height:
            image.generated_height = height
    else:
        assert(image.source == 'GENERATED')
        assert(image.size[0] == width)
        assert(image.size[1] == height)

    image.pixels = pixels
    image.preview.reload()

"""
Create image pixel update job.
get_image is a callable that takes a scene argument and returns an image datablock or None.
pixels is raw RGBA pixel data that can be written to the image datablock.
width and height are new image size values, only used if allow_resize is set to True.
"""
def enqueue_image_pixel_update(q, get_image, pixels, width, height, allow_resize=False):
    # Clear queue
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break

    def job(scene):
        image = get_image(scene)
        if image is not None:
            update_image_pixels(image, pixels, width, height, allow_resize)

    try:
        q.put_nowait(job)
    except queue.Full:
        pass

"""
Check if image pixel update is available and execute it.
Returns True if image pixel data was updated.
"""
def execute_image_pixel_update(q, scene):
    while not q.empty():
        try:
            job = q.get_nowait()
            job(scene)
            return True
        except queue.Empty:
            return False
    return False

def execute_all_image_pixel_updates(scene):
    execute_image_pixel_update(sampling_queue, scene)
    execute_image_pixel_update(pointspread_queue, scene)

"""
Convert data array into image pixels.
"""
def ndarray_to_pixels(array, mapping=(0.0, 1.0)):
    assert(len(array.shape) == 2)

    w = array.shape[0]
    h = array.shape[1]
    values = np.clip(array / (mapping[1] - mapping[0]) - mapping[0], mapping[0], mapping[1]).astype(np.float32)

    imgdata = np.dstack((values, values, values, np.ones(values.shape)))
    return imgdata.flatten().tolist()

def compute_sampling_image(scene, antennas):
    if len(antennas) < 2:
        return False
    w = scene.interferometry.image_width
    h = scene.interferometry.image_height
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
    pointspread = fft.irfft2(sampling, s=(w, h), norm="ortho")

    enqueue_image_pixel_update(
        sampling_queue,
        get_image=lambda scene: scene.interferometry.get_sampling_image(create=True),
        pixels=ndarray_to_pixels(sampling),
        width=sampling.shape[0],
        height=sampling.shape[1],
        allow_resize=True,
        )
    enqueue_image_pixel_update(
        pointspread_queue,
        get_image=lambda scene: scene.interferometry.get_pointspread_image(create=True),
        pixels=ndarray_to_pixels(pointspread, mapping=(0.0, 0.1)),
        width=pointspread.shape[0],
        height=pointspread.shape[1],
        allow_resize=True,
        )

    return True