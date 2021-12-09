import os.path
from numpy import empty_like
from skimage.io import imread, imsave
from skimage.exposure import adjust_gamma
from magicgui import magicgui, event_loop

"""
See: https://scikit-image.org/docs/dev/api/skimage.exposure.html#skimage.exposure.adjust_gamma

Adjusts gamma of the input channel pixelwise according to O = I**gamma.
This extra version of this script is a good example on how to quickly implement a GUI popup with MagicGui.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
PySide2, QtPy
MagicGui (note: version > 0.1.6 requires Python > 3.6)

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
    
    #collect gamma with GUI
    with event_loop():
        gui = get_gamma.Gui(show=True)
        gui.called.connect(lambda x: gui.close())
    
    gamma_value = gui.gamma
    output_data = adjust_gamma(image_data, gamma_value, 1)
    imsave(result_location, output_data)


# decorate your function with the @magicgui decorator
@magicgui(call_button="Run")
def get_gamma(gamma = 0.75):
    pass


if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test_8b.tif'
    params['resultPath'] = 'testResult.tif'
    params['gamma'] = 0.75
    
    run(params)

