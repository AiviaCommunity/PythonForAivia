# -------- Activate virtual environment -------------------------
import os
import ctypes
import sys
from pathlib import Path

def search_activation_path():
    for i in range(5):
        final_path = str(Path(__file__).parents[i]) + '\\env\\Scripts\\activate_this.py'
        if os.path.exists(final_path):
            return final_path
    return ''

activate_path = search_activation_path()
if os.path.exists(activate_path):
    exec(open(activate_path).read(), {'__file__': activate_path})
    print(f'Aivia virtual environment activated\nUsing python: {activate_path}')
else:
    error_mess = f'Error: {activate_path} was not found.\n\nPlease check that:\n' \
                 f'   1/ The \'FirstTimeSetup.py\' script was already run in Aivia,\n' \
                 f'   2/ The current python recipe is in one of the "\\PythonEnvForAivia\\" subfolders.'
    ctypes.windll.user32.MessageBoxW(0, error_mess, 'Error', 0)
    sys.exit(error_mess)
# ---------------------------------------------------------------

from skimage.io import imread, imsave
from skimage.exposure import adjust_gamma
from magicgui import magicgui

"""
See: https://scikit-image.org/docs/dev/api/skimage.exposure.html#skimage.exposure.adjust_gamma

Adjusts gamma of the input channel pixelwise according to O = I**gamma.
This extra version of this script is a good example on how to quickly implement a GUI popup with MagicGui.

Requirements (managed by the virtual environment)
------------
numpy
scikit-image
PySide2, QtPy
MagicGui (Warning: the code below is for version 0.3.x and python 3.9)

Parameters
----------
Input Image : Aivia channel
    Input channel to use for the transform.

Gamma : double
    Value to use for the gamma transform.

Returns
-------
Aivia channel
    Result of the transform

"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [OUTPUT Name:resultPath Type:string DisplayName:'Gamma Adjusted']
def run(params):
    image_location = params['inputImagePath']
    result_location = params['resultPath']
    
    if not os.path.exists(image_location):
        print(f'Error: {image_location} does not exist')
        return
        
    image_data = imread(image_location)
    
    # collect gamma with GUI
    get_gamma.show(run=True)
    # get_gamma.called.connect(lambda x: get_gamma.close()) # Generate a warning, callback defined as a function below

    gamma_value = get_gamma.gamma.value
    output_data = adjust_gamma(image_data, gamma_value, 1)
    imsave(result_location, output_data)


# decorate your function with the @magicgui decorator
@magicgui(call_button="Run")
def get_gamma(gamma = 0.75):
    pass


@get_gamma.called.connect
def close_GUI_callback():
    get_gamma.close()


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test_8b.tif'
    params['resultPath'] = 'testResult.tif'
    params['gamma'] = 0.75
    
    run(params)

# v1.01: - New virtual env code for auto-activation
