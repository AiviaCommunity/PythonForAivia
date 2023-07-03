# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path

def search_activation_path():
    for i in range(5):
        final_path = str(Path(__file__).parents[i]) + '\\env\\Scripts\\activate_this.py'
        if os.path.exists(final_path):
            return final_path
    return ''

activate_path = search_activation_path()
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    error_mess = f'Error: {activate_path} was not found.\n\nPlease check that:\n' \
                 f'   1/ The \'FirstTimeSetup.py\' script was already run in Aivia,\n' \
                 f'   2/ The current python recipe is in one of the "\\PythonEnvForAivia\\" subfolders.'
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    sys.exit(error_mess)
# ---------------------------------------------------------------

from magicgui import magicgui
import numpy as np
from skimage.io import imread, imsave
from skimage import draw

"""
Create shapes in 2D or 2D+t images.

Documentation
------------
https://scikit-image.org/docs/stable/api/skimage.draw.html
https://scikit-image.org/docs/stable/auto_examples/edges/plot_shapes.html#sphx-glr-auto-examples-edges-plot-shapes-py

Requirements
------------
numpy
scikit-image
magicgui

Parameters
----------
Input channel:
    Any channel, just passing dimensions and pixel resolution used for shape size definition.

Returns
-------
Channel in Aivia
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Shape mask']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
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

    image_data = imread(image_location)
    dims = image_data.shape
    bitdepth = image_data.dtype
    bitdepth_max = np.iinfo(bitdepth).max
    print('-- Input dimensions (expected (T,) (Z,) Y, X): ', np.asarray(dims), ' --')

    # Define shape
    dim_shift = 1 if tCount > 1 else 0
    max_x = dims[1 + dim_shift]
    max_y = dims[dim_shift]
    image_center = get_image_center(max_y, max_x)       # WARNING: Y, X due to shape constraint

    # SHAPE DEFINITIONS ------------------------
    def draw_disk(shape_YX_pos, shape_width, image_XYshape):
        return draw.disk(shape_YX_pos, shape_width / 2, shape=image_XYshape)

    def draw_circle(shape_YX_pos, shape_width, image_XYshape):
        return draw.circle_perimeter(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_width / 2), shape=image_XYshape)

    def draw_circle_aa(shape_YX_pos, shape_width, image_XYshape):
        return draw.circle_perimeter_aa(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_width / 2), shape=image_XYshape)

    def draw_ellipse(shape_YX_pos, shape_width, shape_height, image_XYshape):       # X/Y are inverted!!
        return draw.ellipse(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_height / 2), int(shape_width / 2),
                            shape=image_XYshape)

    def draw_ellipse_perimeter(shape_YX_pos, shape_width, shape_height, image_XYshape):
        return draw.ellipse_perimeter(int(shape_YX_pos[0]), int(shape_YX_pos[1]), int(shape_height / 2), int(shape_width / 2),
                                      shape=image_XYshape)

    def draw_rectangle(shape_YX_pos, rect_width, rect_height, image_XYshape):
        rect_center = int(shape_YX_pos[0]), int(shape_YX_pos[1])
        rect_start = int(rect_center[0] - (rect_height / 2)), int(rect_center[1] - (rect_width / 2))
        rect_end = int(rect_center[0] + (rect_height / 2)), int(rect_center[1] + (rect_width / 2))
        return draw.rectangle(start=rect_start, end=rect_end, shape=image_XYshape)

    def draw_rectangle_perimeter(shape_YX_pos, rect_width, rect_height, image_XYshape):
        rect_center = int(shape_YX_pos[0]), int(shape_YX_pos[1])
        rect_start = int(rect_center[0] - (rect_height / 2)), int(rect_center[1] - (rect_width / 2))
        rect_end = int(rect_center[0] + (rect_height / 2)), int(rect_center[1] + (rect_width / 2))
        return draw.rectangle_perimeter(start=rect_start, end=rect_end, shape=image_XYshape)

    def draw_line(shape_YX_pos, X_end, Y_end, image_XYshape):
        line_start_X = int(shape_YX_pos[1])
        line_start_Y = int(shape_YX_pos[0])
        line_end_X = int(X_end)
        line_end_Y = int(Y_end)
        return draw.line(line_start_Y, line_start_X, line_end_Y, line_end_X)

    shapes = {'Disk': draw_disk, 'Circle': draw_circle, 'Smoothed Circle': draw_circle_aa,
              'Ellipse (plain shape)': draw_ellipse, 'Ellipse contour': draw_ellipse_perimeter,
              'Rectangle (plain shape)': draw_rectangle, 'Rectangle contour': draw_rectangle_perimeter,
              'Line': draw_line}
    # /SHAPE DEFINITIONS -----------------------

    # GUI
    @magicgui(layout='vertical', persist=True,
              shape_c={'label': 'Shape: ', 'choices': shapes.keys()},
              shape_center_X_c={'label': 'X coordinate of shape center // \n'
                                         'X start coordinate for Line drawing (calibrated from original image): ',
                                'max': max_x},
              shape_center_Y_c={'label': 'Y coordinate of shape center // \n'
                                         'Y start coordinate for Line drawing (calibrated from original image): ',
                                'max': max_y},
              shape_width_c={'label': 'Width // \n'
                                      'X end coordinate for Line drawing (calibrated from original image): ',
                             'max': max_x},
              shape_height_c={'label': '[Optional] Height // \n'
                                       'Y end coordinate for Line drawing (calibrated from original image): ',
                              'max': max_y},
              reset_default={'widget_type': 'PushButton',
                             'label': 'Reset values to default (shape in image center)'},
              spacer={'widget_type': 'Label', 'label': '  '},
              call_button="Draw shape")
    def gui(shape_c=[*shapes][0], shape_center_X_c=image_center[1], shape_center_Y_c=image_center[0],
            shape_width_c=image_center[1], shape_height_c=image_center[0], reset_default=False, spacer=' '):
        pass

    def reset_gui_defaults():
        gui.shape_center_X_c.value = image_center[1] * XY_cal
        gui.shape_center_Y_c.value = image_center[0] * XY_cal
        gui.shape_width_c.value = image_center[1] * XY_cal
        gui.shape_height_c.value = image_center[0] * XY_cal

        gui.reset_default.value = False

    gui.reset_default.changed.connect(lambda x: reset_gui_defaults())
    gui.called.connect(lambda x: gui.close())
    gui.show(run=True)
    selected_shape = gui.shape_c.value
    selected_position = float(gui.shape_center_Y_c.value) / XY_cal, float(gui.shape_center_X_c.value) / XY_cal    # Y, X
    selected_width = gui.shape_width_c.value / XY_cal
    selected_height = gui.shape_height_c.value / XY_cal

    # Collect shape mask indexes
    image_XY_shape = (dims[dim_shift], dims[1 + dim_shift])
    if any([t in selected_shape for t in ['Ellipse', 'Rectangle', 'Line']]):
        draw_args = selected_position, selected_width, selected_height, image_XY_shape
    else:
        draw_args = selected_position, selected_width, image_XY_shape

    shape_np_indexes = shapes[selected_shape](*draw_args)
    if len(shape_np_indexes) == 3:
        rr, cc, val = shape_np_indexes
    else:
        rr, cc = shape_np_indexes
        val = 1

    # Draw shape in numpy array
    output_data = np.zeros_like(image_data)
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


def get_image_center(height, width):
    return height / 2, width / 2


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\2D-TL-toalign.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\output.tif',
              'ZCount': 1,
              'TCount': 16,
              'Calibration': 'XYZT: 1 micrometers, 1 micrometers, 1 micrometers, 1 Default',
              'externalOutput': 1}

    run(params)

# CHANGELOG
# v1.00: - using Skimage.draw shapes. Adding virtual env for GUI
# v1.01: - New virtual env code for auto-activation
