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
    
    # Get masks from any image where positive mask has intensity above or equal 1
    component1 = np.where(RTData == 0, 0, 1).astype(np.uint8)
    component2 = np.where(GTData == 0, 0, 1).astype(np.uint8)
    
    overlap = component1*component2 # Logical AND
    union = component1 + component2 # Logical OR
    
    IoU = overlap.sum()/float(union.sum())
    print(f'___ Intersection over Union = {IoU} ___')    # Value appears in the log if Verbosity option is set to 'Everything'
    
    # Display result too in a popup
    ctypes.windll.user32.MessageBoxW(0, str(IoU), 'Intersection over Union', 0)
    
    # Convert intersection to 8-bit range
    outputData = rescale_intensity(overlap, out_range='uint8').astype(RTData.dtype)
    
    imsave(resultLocation, outputData)
