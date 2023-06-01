import os.path
from skimage.io import imread, imsave
import shlex, subprocess

"""
This is script has no real function (yet) and constitutes more like a diverted way to couple python to Aivia.
It only shows an example of code, from line 41, on how to run any external program.
The example here also shows that calling Aivia.exe to open an image whereas it is already running 
leads to loading the new image in the existing Aivia window.

Requirements
------------
scikit-image

Parameters
----------
Input Image : In this example, it can be any image

Returns
-------
The same image in a new channel 

"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input']
# [OUTPUT Name:resultPath Type:string DisplayName:'Output']
def run(params):
    imageLocation = params['inputImagePath']
    resultLocation = params['resultPath']
    
    # Checking existence of temporary files (individual channels)
    if not os.path.exists(imageLocation):
        print(f'Error: {imageLocation} does not exist')
        return;
        
    # Loading input images
    imgData = imread(imageLocation)
    
    # Save dummy output
    imsave(resultLocation, imgData)
    
    # Run external program
    cmdLine = 'start \"\" \"C:\\Program Files\\DRV Technologies\\Aivia 8.8.2\\Aivia.exe\" \"C:\\Users\\XXX\\Documents\\AIVIA Demo\\__Demo Datasets\\_Wiki_Cell Count-Demo.tif\"'
    
    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)
