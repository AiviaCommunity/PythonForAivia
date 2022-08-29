# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path
parentFolder = str(Path(__file__).parent.parent)
activate_path = parentFolder + '\\env\\Scripts\\activate_this.py'
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    # Attempt to still run the script with main Aivia python interpreter
    error_mess = f'Error: {activate_path} was not found.\nPlease run the \'FirstTimeSetup.py\' script in Aivia first.'
    ans = ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 1)
    if ans == 2:
        sys.exit(error_mess)
    print('\n'.join(['#' * 40, error_mess,
                     'Now trying to fallback on python environment specified in Aivia options > Advanced.',
                     '#' * 40]))
# ---------------------------------------------------------------

import os.path
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread, imsave

"""
Computes the luminance of an RGB image and returns that as a new channel.

Useful when images are saved as RGB (e.g. histopathology, photographs, etc.)
and the user desires to apply a recipe or pixel classifier to only one
channel, but wishes to retain the maximum amount of information from each.

The luminance has a 30% contribution from the red channel, 59%
contribution from the green channel, and 11% contribution from the
blue channel.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
matplotlib
wxpython or PySide2 (for matplotlib to display charts)

Parameters
----------
Red : Aivia channel
    Red channel.

Green : Aivia channel
    Green channel.

Blue : Aivia channel
    Blue channel.

Histogram : int (bool)
    Boolean to determine whether to display the resulting luminance histogram.
    0 : Do not display
    1 : Display
    Displaying the histogram halts the script until the Matplotlib popup is closed.

Returns
-------
Aivia channel
    Result of the transform
"""

# [INPUT Name:blue_c Type:string DisplayName:'Blue Channel']
# [INPUT Name:green_c Type:string DisplayName:'Green Channel']
# [INPUT Name:red_c Type:string DisplayName:'Red Channel']
# [INPUT Name:histogram Type:int DisplayName:'Show Histogram (0=no, 1=yes)' Default:0 Min:0 Max:1]
# [OUTPUT Name:gray_c Type:string DisplayName:'Luminance']
def run(params):
    red_c = params['red_c']
    blue_c = params['blue_c']
    green_c = params['green_c']
    gray_c = params['gray_c']
    show_histogram = int(params['histogram'])
    if not os.path.exists(red_c):
        print(f'Error: {red_c} does not exist')
        return;
    if not os.path.exists(blue_c):
        print(f'Error: {blue_c} does not exist')
        return;
    if not os.path.exists(green_c):
        print(f'Error: {green_c} does not exist')
        return;
        
    red_data = imread(red_c)
    blue_data = imread(blue_c)
    green_data = imread(green_c)
    
    gray_data = np.empty_like(red_data)
    
    print(f'Red: {red_data.nbytes}')
    print(f'Blue: {blue_data.nbytes}')
    print(f'Green: {green_data.nbytes}')
    print(f'Gray: {gray_data.nbytes}')
    
    gray_data = (0.3*red_data + 0.59*green_data + 0.11*blue_data).astype(red_data.dtype)
    
    if show_histogram == 1:
        ax = plt.hist(gray_data.ravel(), bins=256)
        plt.show()

    imsave(gray_c, gray_data)


if __name__ == '__main__':
    params = {}
    run(params)
