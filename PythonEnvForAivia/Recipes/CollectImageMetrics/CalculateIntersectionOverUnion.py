import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.exposure import rescale_intensity
import ctypes

"""
Calculates Intersection over Union value considering intensity above or equal 1 as a positive mask

Side note: IoU values are output in the log (File > Options > Logging > Open)
To be able to see the printed info in the log file, set:
File > Options > Logging > Verbosity = everything

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
ctypes (comes with Aivia installer)

Parameters
----------
First input: image to compare (e.g.Deep Learning restored image)
Second input: reference (e.g. Ground Truth image)

Returns
-------
New channel to show intersection mask.
Pressing CTRL+C after the popup window appears allow you to copy the text in the window.

"""


# [INPUT Name:inputGTImagePath Type:string DisplayName:'Input Ground Truth Mask']
# [INPUT Name:inputRTImagePath Type:string DisplayName:'Input Mask']
# [OUTPUT Name:resultPath Type:string DisplayName:'Intersection Mask']
def run(params):
    RTimageLocation = params['inputRTImagePath']
    GTimageLocation = params['inputGTImagePath']
    resultLocation = params['resultPath']
    
    # Checking existence of temporary files (individual channels)
    if not os.path.exists(RTimageLocation):
        print(f'Error: {RTimageLocation} does not exist')
        return
    if not os.path.exists(GTimageLocation):
        print(f'Error: {GTimageLocation} does not exist')
        return
    
    # Loading input images
    RTData = imread(RTimageLocation)
    GTData = imread(GTimageLocation)
    
    # Force binary via > 0
    mask1 = RTData > 0
    mask2 = GTData > 0

    intersection_mask = np.logical_and(mask1, mask2)
    intersection = intersection_mask.sum()
    union = np.logical_or(mask1, mask2).sum()

    if union == 0:
        IoU = 0.0
    else:
        IoU = intersection / union

    print(f'___ Intersection over Union = {IoU} ___')    # Value appears in the log if Verbosity option is set to 'Everything'
    
    # Display result too in a popup
    if not 'groundTruthValue_2' in params.keys():
        ctypes.windll.user32.MessageBoxW(0, str(IoU), 'Intersection over Union', 0)
    
    # Convert intersection to 8-bit range
    outputData = intersection_mask.astype(RTData.dtype) * np.iinfo(RTData.dtype).max
    
    imsave(resultLocation, outputData)
    
    return str(IoU)
