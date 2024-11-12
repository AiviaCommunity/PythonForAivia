import os.path
import sys
import numpy as np
from tifffile import imread, imsave
import ctypes

"""
Various arithmetics to be applied to one channel.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
tifffile (installed with scikit-image)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the processing.

Operation : int
    Number-coded arithmetics action (0=multiply, 1=divide, 2=add, 3=subtract).

Threshold : int
    Grayvalue for the arithmetics.


Returns
-------
Aivia objects
    Result of the process.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:value Type:int DisplayName:'Value' Default:0 Min:0 Max:65535]
# [INPUT Name:actionType Type:int DisplayName:'Operation (0=multiply, 1=divide, 2=add, 3=subtract)' Default:0 Min:0 Max:65535]
# [OUTPUT Name:resultImagePath Type:string DisplayName:'Processed Image']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultImagePath']
    operation_type = int(params['actionType'])
    value = float(params['value'])
    tCount = int(params['TCount'])
    zCount = int(params['ZCount'])
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return

    image_data = imread(image_location)
    d_type = image_data.dtype
    dims = image_data.shape

    output_data = np.empty(image_data.shape, dtype=d_type)
    axes = ''

    # 3D+T
    if tCount > 1 and zCount > 1:
        print(f"Applying to 3D+T case with dims: {image_data.shape}")
        for t in range(0, dims[0]):
            output_data[t, :, :, :] = process_data(image_data[t, :, :, :], operation_type, value).astype(d_type)
        axes = 'TZYX'

    # 2D +/- T and 3D
    else:
        print(f"Applying to 2D/3D case with dims: {image_data.shape}")
        output_data = process_data(image_data, operation_type, value).astype(d_type)
        if zCount > 1:
            axes = 'ZYX'
        else:
            axes = 'TYX' if tCount > 1 else 'YX'

    imsave(result_location, output_data, metadata={'axes': axes}, ome=True)


def process_data(data, op_type: int, value: int):
    out_data = None
    if op_type == 0:  # MULTIPLY
        out_data = np.float32(data) * value
    elif op_type == 1:  # DIVIDE
        if value == 0:
            sys.exit('Division by zero is not possible.')
        out_data = np.float32(data) / value
    elif op_type == 2:  # ADD
        out_data = np.float32(data) + value
    elif op_type == 3:  # SUBTRACT
        out_data = np.float32(data) - value
    elif op_type > 3:
        sys.exit('Wrong selection of operation type')
        
    # Clipping data only if 8 or 16 bit
    if any(data.dtype == dtp for dtp in [np.uint8, np.uint16]):
        if np.max(out_data) > np.iinfo(data.dtype).max or np.min(out_data) < 0:
            out_data = out_data.clip(0, np.iinfo(data.dtype).max)
            print(f'Clipping data to fit the {data.dtype} range.')

    return out_data


def Mbox(title, text):
    return ctypes.windll.user32.MessageBoxW(0, text, title, 0)


if __name__ == '__main__':
    # Commandline arguments: image_path,  
    params = {'inputImagePath': r'D:\PythonCode\_tests\3D Object Analysis From Seeds_test_seeds.aivia.tif',
              'resultImagePath': r'D:\PythonCode\_tests\test.tif',
              'Calibration': 'XYZT: 0.3225 Micrometers, 0.3225 Micrometers, 1 Micrometers, 1 Default',
              'ZCount': 8, 'TCount': 1, 'actionType': 2, 'value': 2}
    run(params)

# CHANGELOG
#   v1_00: - From Threshold_for_3DObjects.py. Compatible with 32 bit images
#   v1_10: - Adding ome=True tag with imwrite for Aivia 13.0.0 compatibility 
