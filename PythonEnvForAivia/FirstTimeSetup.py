import os.path
import subprocess
import pathlib
from pathlib import Path
from shutil import copyfile
import sys
import ctypes
from skimage.io import imread, imsave
import numpy as np

"""
This Aivia python recipe will create the required virtual environment for all recipes available
on our GitHub: https://github.com/AiviaCommunity/PythonForAivia.

Unzip the content of PythonEnvForAivia.zip in a folder WITHOUT admin access restrictions.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Any 2D Image']
# [OUTPUT Name:outputImagePath Type:string DisplayName:'To Delete']
def run(params):

    envDir_ = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'env'
    pythonExec_ = envDir_ / 'Scripts/python.exe'

    if not os.path.exists(pythonExec_):
        # create a virtual environment
        envDir_.mkdir(parents=False, exist_ok=True)
        subprocess.check_call([str(Path(sys.executable).parent / 'Scripts/virtualenv.exe'), f'{envDir_}'])
        
        # copy essential python packages(python312.zip) to virtual environment
        # see https://github.com/pypa/virtualenv/issues/1185
        if not os.path.exists(envDir_/'Scripts/python312.zip'):
            copyfile(Path(sys.executable).parent / 'python312.zip', envDir_/'Scripts/python312.zip')

        # install requirements
        mess = 'Python packages will now be installed. An internet connection is needed.\n\n' \
               'You can follow the addition of the packages in the following subfolder:\n' + str(envDir_) + \
               '\\Lib\\site-packages'
        Mbox('Starting installing python packages', mess, 0)

        pip_path = envDir_ / 'Scripts' / 'pip.exe'
        requirement_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
        # subprocess.check_call(
        #     [str(pip_path), 'install', 'setuptools==70.0.0'])
        subprocess.check_call(
            [str(pip_path), 'install', '-r', str(requirement_dir/'requirements.txt')])
                    
    # Check if python exists
    if not os.path.exists(pythonExec_):
        raise ValueError(f'Error: {pythonExec_} does not exist')

    # Log
    message = f'Python was installed here:\n{pythonExec_}'
    print(message)
    
    # Load image, to avoid error displayed in Aivia
    inputImagePath_ = params['inputImagePath']
    outputImagePath_ = params['outputImagePath']
    
    input_img = imread(inputImagePath_)    
    imsave(outputImagePath_, np.zeros_like(input_img))
    

def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    

if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test_8b.tif'
    params['outputImagePath'] = 'testResult.tif'

    run(params)
