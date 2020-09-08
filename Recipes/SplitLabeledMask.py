import ctypes
import sys
import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage import segmentation

"""
Separates labeled objects in a mask (2D or 3D).
For instance, CellPose and StarDist output masks where objects can touch each other.
In Aivia, objects need to be separated to be measurable.

Works only when there is no time dimension (yet).

Doc for boundaries function:
https://scikit-image.org/docs/stable/api/skimage.segmentation.html#skimage.segmentation.find_boundaries

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Parameters
----------
Input channel:
    Input channel with labeled mask and touching objects.

Returns
-------
New mask with separated labeled objects

"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Labeled Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:'Split Labeled Mask']
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

    # Checking image is not 2D+t or 3D+t
    if len(dims) > 3 or (len(dims) == 3 and tCount > 1):
        message = 'Error: Cannot be applied to timelapses.'
        Mbox('No info found', message, 0)
        sys.exit(message)

    output_data = np.empty_like(image_data)

    # Detecting boundaries to be subrtracted to original image
    boundaries = segmentation.find_boundaries(image_data)
    output_data = image_data - image_data * boundaries

    imsave(result_location, output_data)


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputImagePath': 'D:\\python-tests\\test.aivia.tif',
              'resultPath': 'D:\\python-tests\\test.tif',
              'TCount': 1}

    run(params)
