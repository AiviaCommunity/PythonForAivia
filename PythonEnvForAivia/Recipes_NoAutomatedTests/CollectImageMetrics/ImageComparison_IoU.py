import os.path
import numpy as np
from skimage.io import imread, imsave
from skimage.exposure import rescale_intensity
import ctypes

"""
Calculates Intersection over Union value considering intensity above or equal 1 as a positive mask.
Output is written in a text file in the same folder as this script.

Side note: IoU values are also output in the log
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
New channel to show intersection mask

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
    
    overlap = np.logical_and(component1, component2)
    union = np.logical_or(component1, component2)

    IoU = overlap.sum()/float(union.sum())
    print(f'___ Intersection over Union = {IoU} ___')    # Value appears in the log if Verbosity option is set to 'Everything'
    
    # Display result in a popup too
    mess = f"Intersection over Union:\n{str(IoU)}"
    ctypes.windll.user32.MessageBoxW(0, mess, 'Result', 0)

    # output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_p = os.path.join(script_dir, 'ImageComparison_IoU_result.txt')

    # Save as text file and open
    with open(out_p, "w") as f:
        f.write(mess)
    os.startfile(out_p)

    # Convert intersection to initial range
    outputData = rescale_intensity(overlap, out_range='uint8').astype(RTData.dtype)
    
    # imsave(resultLocation, outputData)
    imsave(resultLocation, union)


if __name__ == '__main__':
    params = {'inputRTImagePath': r"D:\PythonCode\_tests\XY_378x255_1ch_8bit_binarymask_nucleus_APP-nuc-separation_A14.0.aivia.tif",
              'inputGTImagePath': r"D:\PythonCode\_tests\XY_378x255_1ch_8bit_binarymask_nucleus_APP-nuc-separation_IoU-TEST_A15.0.aivia.tif",
              'resultPath': r"D:\PythonCode\_tests\dummy_to_delete.tif"}
    run(params)


# CHANGELOG
# v1_00 PM: - Inputs should be masks / output is in the log + popup window
# v1_01 PM: - popup window is text-selectable -----------
# v2_00 PM: - Discarded tkinter, replaced with Win lib ctypes. Function was wrong in previous version.
