import ctypes
import sys
import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.measure import label
from skimage.segmentation import random_walker
from skimage.util import img_as_ubyte, img_as_uint
import time

"""
Creates 3D objects from seeds. Propagation of seeds is limited by input mask.
If input mask is not binary, threshold input value is used (exclusive).

Works only when there is no time dimension (yet).

Docs:
https://scikit-image.org/docs/stable/api/skimage.segmentation.html#skimage.segmentation.random_walker

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes

Parameters
----------
Input channels:
    Whole sample mask
    Seeds binary mask

Returns
-------
Object Set in Aivia

Note: replace output with one of the line below to change output type (objects or mask)
# [OUTPUT Name:resultPath Type:string DisplayName:'Labeled Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:’Objects from seeds’ Objects:3D MinSize:0.5 MaxSize:50000.0]
"""

# [INPUT Name:inputSeedsImage Type:string DisplayName:'Seeds Binary Mask']
# [INPUT Name:inputMaskImage Type:string DisplayName:'Whole Sample Mask']
# [INPUT Name:thresholdVal Type:int DisplayName:'Intensity Threshold if not a mask' Default:1 Min:0 Max:65535]
# [OUTPUT Name:resultPath Type:string DisplayName:'Labeled Mask']
def run(params):
    whole_mask_p = params['inputMaskImage']
    seeds_mask_p = params['inputSeedsImage']
    threshold = int(params['thresholdVal'])
    result_location = params['resultPath']
    tCount = int(params['TCount'])
    if not os.path.exists(whole_mask_p):
        print(f"Error: {whole_mask_p} does not exist")
        return

    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front

    # Calculating ratio between XY and Z                # Expecting only 'Micrometers' in this code
    XY_cal = float(pixel_cal[0].split(' ')[0])
    Z_cal = float(pixel_cal[2].split(' ')[0])
    cal_ratio = Z_cal / XY_cal

    t0 = time.perf_counter()
    whole_mask = imread(whole_mask_p)
    # Check if a mask, otherwise apply threshold
    if len(np.unique(whole_mask)) > 2:
        whole_mask = np.where(whole_mask > threshold, 1, 0)
        print(f'Detected more than two values in mask.\n'
              f'Using provided threshold (= {threshold}) to transform the image as a mask.')

    t1 = time.perf_counter()
    print('Creating whole sample mask done in {:0.2f} seconds'.format(t1 - t0))

    seeds_mask = imread(seeds_mask_p)
    dims = whole_mask.shape
    print('-- Input dimensions (expected (Z), Y, X): ', np.asarray(dims), ' --')

    # Checking image is not 2D/2D+t or 3D+t
    if len(dims) == 2 or (len(dims) == 3 and tCount > 1):
        message = 'Error: Cannot be applied to timelapses or 2D images.'
        Mbox('Error', message, 0)
        sys.exit(message)

    # Seed binary mask needs to be transformed as labeled mask
    labeled_seeds = label(seeds_mask)
    t2 = time.perf_counter()
    print('Creating labels from seeds mask done in {:0.2f} seconds'.format(t2 - t1))

    # Important? Set to -1 all pixels not in the whole sample mask
    labeled_seeds[whole_mask == 0] = -1

    # Performing seeds-guided segmentation of the whole sample mask
    # mode options = ‘cg’, ‘cg_j’, ‘cg_mg’, ‘bf’
    labeled_mask = random_walker(whole_mask, labeled_seeds, mode='cg_j', copy=True, spacing=(cal_ratio, 1.0, 1.0))
    t3 = time.perf_counter()
    print('Random Walker segmentation done in {:0.2f} seconds'.format(t3 - t2))
    
    # Conversion from 32 bit to 8 or 16 bit
    if whole_mask.dtype == np.uint16:
        final_mask = img_as_uint(labeled_mask)
    else:
        final_mask = img_as_ubyte(labeled_mask)

    imsave(result_location, final_mask)


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


if __name__ == '__main__':
    params = {'inputMaskImage': r'D:\PythonCode\_tests\3D Object Analysis From Seeds_test_mask.aivia.tif',
              'inputSeedsImage': r'D:\PythonCode\_tests\3D Object Analysis From Seeds_test_seeds.aivia.tif',
              'resultPath': r'D:\PythonCode\_tests\test.tif',
              'Calibration': 'XYZT: 0.3225 Micrometers, 0.3225 Micrometers, 1 Micrometers, 1 Default',
              'TCount': 1, 'thresholdVal': 0}

    run(params)

# CHANGELOG
#   v1_00: - From Objects_From_3D_Labeled_Mask_1_00.py
