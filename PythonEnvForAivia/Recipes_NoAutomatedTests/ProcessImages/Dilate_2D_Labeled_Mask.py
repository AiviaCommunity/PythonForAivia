import ctypes
import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.segmentation import expand_labels

"""
Dilate 2D labeled masks.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes

Parameters
----------
Input channel:
    Input channel to be dilated. Prefer a binary mask.

Returns
-------
Channel in Aivia
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Labeled Mask']
# [INPUT Name:dilation Type:int DisplayName:'Dilate distance (pixels)' Default:1 Min:0 Max:65535]
# [OUTPUT Name:resultPath Type:string DisplayName:'Dilated Labeled Mask']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    zCount = int(params['ZCount'])
    tCount = int(params['TCount'])
    dilation = int(params['dilation'])

    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    if zCount > 1:
        Mbox('Error', 'This recipes currently only supports 2D images.', 0)
        return

    lbl_data = imread(image_location)
    dims = lbl_data.shape
    print('-- Input dimensions (expected (T,) (Z,) Y, X): ', np.asarray(dims), ' --')

    output_data = expand_labels(lbl_data, dilation)

    imsave(result_location, output_data)


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\3D-image.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\test.tif',
              'ZCount': 51, 'TCount': 1,
              'threshold': 1, 'dilation': 3}

    run(params)

# CHANGELOG
#   v1_00: - Comes from Dilate_3D_v1_00.py
