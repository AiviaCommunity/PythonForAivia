import ctypes
import sys
import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage import segmentation

"""
Separates labeled objects in a 3D mask and creates measurable objects in Aivia.
For instance, CellPose and StarDist output masks where objects can touch each other.
In Aivia, objects need to be separated to be measurable.

WARNING: the boundary detection leads to a large cut (~3 pixels wide) between objects.

Works only when there is no time dimension (yet).

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes

Parameters
----------
Input channel:
    Input channel with labeled mask and touching objects.

Returns
-------
Object Set in Aivia

Note: replace output with one of the line below to change output type (objects or mask)
# [OUTPUT Name:resultPath Type:string DisplayName:'Split Labeled Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:’Objects from labels’ Objects:3D MinSize:0.5 MaxSize:50000.0]
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Labeled Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:’Objects from labels’ Objects:3D MinSize:0.5 MaxSize:50000.0]
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    tCount = int(params['TCount'])
    if not os.path.exists(image_location):
        print(f"Error: {image_location} does not exist")
        return

    image_data = imread(image_location)
    dims = image_data.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D/2D+t or 3D+t
    if len(dims) == 2 or (len(dims) == 3 and tCount > 1):
        message = 'Error: Cannot be applied to timelapses or 2D images.'
        Mbox('Error', message, 0)
        sys.exit(message)

    output_data = np.empty_like(image_data)

    # Detecting boundaries to be subtracted to original image
    boundaries = segmentation.find_boundaries(image_data, mode='outer')
    output_data = np.where(boundaries, 0, image_data)

    imsave(result_location, output_data)
    print('Successfully saved output channel')


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\3D-image.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\test.tif',
              'TCount': 1}

    run(params)

# CHANGELOG
#   v1_00: - From Split_3D_Labeled_Mask_1_10.py
