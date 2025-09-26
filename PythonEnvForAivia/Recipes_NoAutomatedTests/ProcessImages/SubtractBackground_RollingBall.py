import math
import numpy as np
from tifffile import imread, imwrite
from skimage.restoration import rolling_ball
from skimage.transform import rescale
from skimage.util import img_as_ubyte, img_as_uint
import ctypes

"""
See: https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.rolling_ball

Process a single channel image to subtract the background.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the processing.

Radius : int
    Size of kernel used.

Returns
-------
Aivia image
    Result of the transform.
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:radius Type:int DisplayName:'Radius (calibrated distance)' Default:0 Min:0 Max:100]
# [OUTPUT Name:resultImagePath Type:string DisplayName:'Processed Image']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultImagePath']
    radius = int(params['radius'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])

    pixel_cal_tmp = params['Calibration']
    pixel_cal = pixel_cal_tmp[6:].split(', ')           # Expects calibration with 'XYZT: ' in front
    XY_cal = float(pixel_cal[0].split(' ')[0])

    px_radius = round(radius / XY_cal)
        
    image_data = imread(image_location)
    dims = image_data.shape
    
    processed = np.empty_like(image_data)
    parameters = {'radius': px_radius if px_radius > 0 else 1}
    print(f"Pixel-based radius for rolling ball: {parameters['radius']}")

    # xD+T
    if tCount > 1:
        if zCount == 1:                                                         # 2D+T
            print(f"Applying to 2D+T case with dims: {image_data.shape}")
            for t in range(dims[0]):
                if dims[0] == tCount:
                    processed[t, :, :] = process_img(image_data[t, :, :], parameters)
                    axes = 'TYX'  # Format from tifffile
                else:
                    processed[:, :, t] = process_img(image_data[:, :, t], parameters)
                    axes = 'YXT'
                    print('Processing an unconventional timelapse with YXT dimensions')
        else:                                                                            # 3D+T
            print(f"Applying to 3D+T case with dims: {image_data.shape}")
            for t in range(dims[0]):
                for z in range(dims[1]):
                    if dims[0] == tCount:
                        processed[t, z, :, :] = process_img(image_data[t, z, :, :], parameters)
                        axes = 'TZYX'  # Format from tifffile
                    else:
                        processed[z, :, :, t] = process_img(image_data[z, :, :, t], parameters)
                        axes = 'ZYXT'
                        print('Processing an unconventional timelapse with ZYXT dimensions')

    # 2D and 3D
    elif tCount == 1:
        if zCount == 1:                                                     # 2D
            print(f"Applying to 2D case with dims: {image_data.shape}")
            processed = process_img(image_data, parameters)
            axes = 'YX'
        else:                                                               # 3D
            print(f"Applying to 3D case with dims: {image_data.shape}")
            for z in range(dims[0]):
                processed[z, :, :] = process_img(image_data[z, :, :], parameters)
            axes = 'ZYX'

    # Conversion to 8 or 16 bit
    if image_data.dtype == np.uint16:
        final_mask = img_as_uint(processed)
    else:
        final_mask = img_as_ubyte(processed)

    print(f'Converting processed image from {processed.dtype} (min={np.min(processed)}, max={np.max(processed)})'
          f' to {final_mask.dtype} (min={np.min(final_mask)}, max={np.max(final_mask)})')

    imwrite(result_location, final_mask, metadata={'axes': axes})


def process_img(img_array, params: dict):
    # Downsampling image if radius is to large
    downsamp_factor = 1
    division_factor = 2
    interpol_mode = 1  # 0: Nearest-neighbor, 1: Bi-linear , 2: Bi-quadratic, 3: Bi-cubic, 4: Bi-quartic, 5: Bi-quintic
    radius_thr = 50

    tmp_radius = params['radius']
    while tmp_radius > radius_thr:
        tmp_radius = math.floor(tmp_radius / division_factor)
        downsamp_factor *= division_factor

    final_radius = tmp_radius

    # Downsampling the image, if needed
    if downsamp_factor > 1:
        proc_img_array = rescale(img_array, 1 / downsamp_factor, interpol_mode, preserve_range=True)
        print(f'--- Downsampling the image {downsamp_factor}x because '
              f'pixel radius {params["radius"]} is higher than defined threshold ({radius_thr}). ---')
    else:
        proc_img_array = img_array

    # Evaluate background map
    downsampled_bkg = rolling_ball(proc_img_array, radius=final_radius).astype(proc_img_array.dtype)

    # Revert image back to original scale
    if downsamp_factor > 1:
        # Calculating back the upsampling factor
        fact_y = img_array.shape[0] / downsampled_bkg.shape[0]
        fact_x = img_array.shape[1] / downsampled_bkg.shape[1]
        upsamp_factor = max(fact_y, fact_x)

        proc_bkg = rescale(downsampled_bkg, upsamp_factor, interpol_mode).astype(img_array.dtype)

        # Transfer to the array
        final_bkg = proc_bkg[:img_array.shape[0], :img_array.shape[1]]

        print(f'--- Upsampling the image {upsamp_factor}x to revert image to original size.'
              f'\nOriginal size:{img_array.shape[0]} * {img_array.shape[1]} ---'
              f'\nRescaled size:{proc_bkg.shape[0]} * {proc_bkg.shape[1]} ---')
    else:
        final_bkg = downsampled_bkg

    # Subtracting the background
    final_data = np.where(img_array >= final_bkg, img_array - final_bkg, 0)

    # final_data = final_bkg

    return final_data


def Mbox(title, text):
    return ctypes.windll.user32.MessageBoxW(0, text, title, 0)


if __name__ == '__main__':
    params = {
        'inputImagePath': r'D:\PythonCode\_tests\XYZ_16x17x19_1ch_8bit_binarymask_synthetic_APP-biofilm_A10.5.aivia.tif',
        'resultImagePath': r'testResult.tif',
        'radius': 1,
        'TCount': 1,
        'ZCount': 19,
        'Calibration': 'XYZT: 0.46 micrometers, 0.46 micrometers, 0.46 micrometers, 1 Default'
    }
    run(params)

# CHANGELOG
# v1_00: - From DetectEdges_v1_00.py
# v1_10: - Adding the possibility to process 3D and 3D + T images
