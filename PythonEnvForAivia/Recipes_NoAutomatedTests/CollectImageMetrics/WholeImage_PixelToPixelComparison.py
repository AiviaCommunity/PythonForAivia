import os.path
import numpy as np
from skimage.io import imread, imsave
import sys
import ctypes

"""
Extracts intensities of two channels, pixel by pixel, and save the list in a csv file.
File is saved where the python script is located.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)

Returns
-------
Dummy channel

"""

# [INPUT Name:inputImagePath2 Type:string DisplayName:'Input Ch2']
# [INPUT Name:inputImagePath1 Type:string DisplayName:'Input Ch1']
# [OUTPUT Name:resultPath Type:string DisplayName:'Channel difference']
def run(params):
    imageLocation1 = params['inputImagePath1']
    imageLocation2 = params['inputImagePath2']
    resultLocation = params['resultPath']
    
    # Checking existence of temporary files (individual channels)
    if not os.path.exists(imageLocation1):
        print(f'Error: {imageLocation1} does not exist')
        return
        
    # Loading input images
    img_data_1 = imread(imageLocation1)
    img_data_2 = imread(imageLocation2)

    # Checking dtype is the same for both input channels
    if img_data_1.dtype != img_data_2.dtype:
        error_mes = "The bit depth of your input channels is not the same. Convert one of them and retry."
        ctypes.windll.user32.MessageBoxW(0, error_mes, 'Error', 0)
        sys.exit(error_mes)

    # Warning for Excel
    px_count = img_data_1.shape[0] * img_data_1.shape[1]
    if px_count > 1048576:
        warn_mess = f"Warning: the pixel number ({px_count}) is higher than the Excel max number of rows (1048576)."
        ctypes.windll.user32.MessageBoxW(0, warn_mess, 'Error', 1)
        print(warn_mess)

    # csv output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_p = os.path.join(script_dir, 'Pixel intensity list_2 channels.csv')

    # Extracting pixels to a csv file
    formatted_data = np.column_stack((img_data_1.ravel(), img_data_2.ravel()))
    np.savetxt(csv_p, formatted_data, fmt='%d', delimiter=",")

    # Saving the difference as new channel
    outputData = (img_data_2 - img_data_1).astype(img_data_1.dtype)
    imsave(resultLocation, outputData)

    # Opening the folder where the script is
    os.startfile(script_dir)


if __name__ == '__main__':
    params = {}
    run(params)


# CHANGELOG
# v1_00 PM: - From ImageComparisonMetrics
