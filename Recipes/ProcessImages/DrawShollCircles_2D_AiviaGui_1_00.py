import os
import ctypes
import sys
import numpy as np
from skimage.io import imread, imsave
from skimage import draw

"""
Create Sholl circles on 2D or 2D+t images.
User can choose center position spacing and number of circles.

Documentation
------------
https://scikit-image.org/docs/stable/api/skimage.draw.html

Requirements
------------
numpy
scikit-image

Parameters
----------
Input channel:
    Any channel, just passing dimensions and pixel resolution used for shape size definition.

Returns
-------
Channel in Aivia
"""

# Manual parameters
selected_shape = 0              # 0 = draw_circle or 1 = draw_circle_aa (anti-aliased)


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [INPUT Name:circleNumber Type:int DisplayName:'Number of circles to draw' Default:10 Min:0 Max:50]
# [INPUT Name:spacing Type:int DisplayName:'Space between circles' Default:10 Min:0 Max:65535]
# [INPUT Name:centerY Type:int DisplayName:'Y coordinate of soma center' Default:0 Min:0 Max:65535]
# [INPUT Name:centerX Type:int DisplayName:'X coordinate of soma center' Default:0 Min:0 Max:65535]
# [OUTPUT Name:resultPath Type:string DisplayName:'Sholl Circles']
def run(params):
    global selected_shape
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    center_X = int(params['centerX'])
    center_Y = int(params['centerY'])
    circle_spacing = int(params['spacing'])
    circle_count = int(params['circleNumber'])
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    external_output = True if 'externalOutput' in params.keys() else False

    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return
    if zCount > 1:
        error_mess = 'Error: script is not compatible with 3D images'
        Mbox('Error', error_mess, 0)
        sys.exit(error_mess)

    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    XY_cal = float(pixel_cal[0].split(' ')[0])

    # Adjusting all values to pixels if image is calibrated
    center_X /= XY_cal
    center_Y /= XY_cal
    circle_spacing /= XY_cal

    image_data = imread(image_location)
    dims = image_data.shape
    bitdepth = image_data.dtype
    bitdepth_max = np.iinfo(bitdepth).max
    print('-- Input dimensions (expected (T,) (Z,) Y, X): ', np.asarray(dims), ' --')

    # Define shape
    dim_shift = 1 if tCount > 1 else 0
    max_x = dims[1 + dim_shift]
    max_y = dims[dim_shift]

    # SHAPE DEFINITIONS ------------------------
    def draw_circle(shape_YX_pos, shape_rad, image_XYshape):
        return draw.circle_perimeter(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_rad), shape=image_XYshape)

    def draw_circle_aa(shape_YX_pos, shape_rad, image_XYshape):
        return draw.circle_perimeter_aa(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_rad), shape=image_XYshape)

    shapes = [draw_circle, draw_circle_aa]
    # /SHAPE DEFINITIONS -----------------------

    # Fixed parameters
    selected_position = center_Y, center_X                          # Y, X !!!
    image_XY_shape = (dims[dim_shift], dims[1 + dim_shift])

    # Loop
    circle_radius = 0
    output_data = np.zeros_like(image_data)

    for c in range(circle_count):
        circle_radius += circle_spacing

        # Collect shape mask indexes
        shape_np_indexes = shapes[selected_shape](selected_position, circle_radius, image_XY_shape)
        if len(shape_np_indexes) == 3:
            rr, cc, val = shape_np_indexes
        else:
            rr, cc = shape_np_indexes
            val = 1

        # Draw shape in numpy array
        if tCount > 1:
            output_data[:, rr, cc] = val * bitdepth_max
        else:
            output_data[rr, cc] = val * bitdepth_max

    if external_output:
        # Defining axes for output metadata and scale factor variable
        axes = 'YX' if tCount == 1 else 'TYX'
        meta_info = {'axes': axes}

        imsave(result_location, output_data, imagej=True, photometric='minisblack', metadata=meta_info)
    else:
        imsave(result_location, output_data)


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\2D-TL-toalign.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'ZCount': 1,
              'TCount': 16,
              'centerX': 60,
              'centerY': 60,
              'spacing': 10,
              'circleNumber': 5,
              'Calibration': 'XYZT: 0.5 micrometers, 1 micrometers, 1 micrometers, 1 Default',
              'externalOutput': 1}

    run(params)

# CHANGELOG
# v1.00: - Code started from DrawShapes_2D_1.00.py, removing magicgui part
