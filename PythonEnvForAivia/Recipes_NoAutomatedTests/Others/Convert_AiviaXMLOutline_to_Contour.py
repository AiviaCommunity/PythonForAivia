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


import wx
import numpy as np
import cv2
from skimage.draw import polygon
from skimage.io import imread, imsave
from xml.dom import minidom
import datetime
import re
import concurrent.futures

# ------ Manual parameters -----------------------
DEFAULT_FOLDER = r''            # For Image browser

"""
Draw contour of XML outlines into a new Aivia channel.

Requirements
------------
wxPython

Returns
-------
    Channel
"""


# [INPUT Name:inputPath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Outline Contour']
def run(params):
    input_p = params['inputPath']
    result_p = params['resultPath']

    sp = os.path.sep

    # Choose files (or rely on an hard coded default folder)
    input_folder = DEFAULT_FOLDER

    # TODO PROD: reactivate
    xml_file = pick_file(input_folder, "Select an XML file exported from Aivia outlines", "XML files (*.xml)|*.xml")
    # xml_file = [input_folder + sp + 'Project001_1outline.xml']

    if len(xml_file) < 1:
        error_msg = 'No files selected. Aborting...'.format(input_folder)
        Mbox('Error', error_msg, 0)
        sys.exit(error_msg)

    # Creates a zero-filled image as output
    if input_p:
        in_img = imread(input_p)
        out_img = np.zeros_like(in_img)
        img_max = np.iinfo(in_img.dtype).max

    # Read XML from Aivia
    all_coordinates = read_LMD_xml_from_Aivia(xml_file)   # from pixel to meters

    # Draw shape
    for coord_list in all_coordinates:
        coords = np.array(coord_list, dtype=int)

        # Draw points defining the shape
        # out_img[coords[:, 1], coords[:, 0]] = img_max

        # Draw plain polygon
        # rr, cc = polygon(coords[:, 1], coords[:, 0], shape=in_img.shape)
        # out_img[rr, cc] = img_max

        # Draw contour only
        cv2.polylines(out_img, [coords], isClosed=False, color=img_max, thickness=1)

    imsave(result_p, out_img)

    mess = 'Conversion is complete.'
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     future = executor.submit(Mbox, 'Process completed', mess, 0)
    print(mess)  # for log


# Ensure closed ring (repeat first point at end)
def close_ring(points: np.ndarray) -> np.ndarray:
    if points.shape[0] < 3:
        raise ValueError("Need at least 3 points for a polygon.")
    if not np.array_equal(points[0], points[-1]):
        points = np.vstack([points, points[0]])
    return points


# Output a list (shapes) of list (coordinates doublet) of list (X and Y) from the XML file. Coordinates in pixels
def read_LMD_xml_from_Aivia(path):
    # Init
    all_coords = []

    parser = minidom.parse(path)
    main_node = parser.getElementsByTagName('ImageData')[0]

    # Collect number of shapes
    shape_count_node = main_node.getElementsByTagName('ShapeCount')[0]
    shape_count = int(shape_count_node.firstChild.data)

    # Loop on individual shapes to retrieve list of coordinates
    for s in range(shape_count):
        node_name = f'Shape_{str(s + 1)}'
        shape_node = main_node.getElementsByTagName(node_name)[0]

        # Retrieve number of points for current shape
        point_count = int(shape_node.getElementsByTagName('PointCount')[0].firstChild.data)

        # Init coordinate list
        shape_coords = []

        for p in range(1, point_count + 1):
            x_coord = float(shape_node.getElementsByTagName(f'X_{p}')[0].firstChild.data)
            y_coord = float(shape_node.getElementsByTagName(f'Y_{p}')[0].firstChild.data)
            shape_coords.append([x_coord, y_coord])

        # Append list of coordinates to output
        all_coords.append(shape_coords.copy())
        shape_coords.clear()

    return all_coords


def pick_file(default_dir, message, format):
    print('Starting wxPython app')
    app = wx.App()

    # Create open file dialog
    openFileDialog = wx.FileDialog(None, message, default_dir, "", format,
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

    openFileDialog.ShowModal()
    filename = openFileDialog.GetPath()
    print("Selected table(s): ", filename)
    openFileDialog.Destroy()
    return filename


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputPath': r"D:\PythonCode\_tests\2Dmask_Crop.aivia.tif", 'resultPath': ''}
    run(params)

# Changelog:
# v1.00: -
