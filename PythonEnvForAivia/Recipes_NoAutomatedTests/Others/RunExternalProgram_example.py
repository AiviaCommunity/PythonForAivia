import os.path
from skimage.io import imread, imsave
import shlex, subprocess
import sys

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


# Get path to the Aivia executable
def getParentDir(curr_dir, level=1):
    for i in range(level):
        parent_dir = os.path.dirname(curr_dir)
        curr_dir = parent_dir
    return curr_dir


exeDir = sys.executable
parentDir = getParentDir(exeDir, level=2)
aivia_path = parentDir + '\\Aivia.exe'

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
    cmdLine = 'start \"\" \"' + aivia_path + '\" \"' + resultLocation + '\"'
    
    args = shlex.split(cmdLine)
    subprocess.run(args, shell=True)


# v1.00: - Automated detection of Aivia version running
