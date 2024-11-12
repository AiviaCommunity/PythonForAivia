import numpy as np
from skimage.io import imread, imsave
import sys
import ctypes

'''
Replicates the first image in a time series to all other time frames.
Useful when a fixed mask needs to be replicated over time.

---
Parameters
    Input: one channel in which first image contains content to replicate
    
---
Output
    New channel with replicated content

'''


# [INPUT Name:inputImagePath Type:string DisplayName:'Channel to replicate']
# [OUTPUT Name:outputImagePath Type:string DisplayName:'Replicated channel']
def run(params):
    inputImagePath_ = params['inputImagePath']
    outputImagePath_ = params['outputImagePath']
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])

    error_mess = ''
    if tCount < 2:
        error_mess = f'Error: detected dimensions do not contain time. (t={tCount})'
        ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
        sys.exit(error_mess)

    # Reading channel (expected T, (Z), Y, X)
    input_data = imread(inputImagePath_)

    output_data = np.zeros_like(input_data)

    # Copying data of first frame
    for t in range(tCount):
        output_data[t, ...] = input_data[0, ...]

    imsave(outputImagePath_, output_data)


if __name__ == '__main__':
    params = {'inputImagePath': r'D:\PythonCode\_tests\3D-TL-toalign.aivia.tif',
              'outputImagePath': r'D:\PythonCode\_tests\3D-replicated.tif',
              'ZCount': 3, 'TCount': 10}

    run(params)
