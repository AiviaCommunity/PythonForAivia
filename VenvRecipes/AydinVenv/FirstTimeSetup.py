import os.path
import subprocess
import pathlib
import time
from pathlib import Path
from shutil import copyfile
import sys
import ctypes
from skimage.io import imread, imsave
import difflib
import shutil

"""
This Aivia python recipe will create the required virtual environment for all recipes available
on our GitHub: https://github.com/AiviaCommunity/PythonForAivia.

Unzip the content of PythonEnvForAivia.zip in a folder WITHOUT admin access restrictions.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Any 2D Image']
# [OUTPUT Name:outputImagePath Type:string DisplayName:'Channel to delete']
def run(params):

    current_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    env_dir = current_dir / 'env'
    pip_path = env_dir / 'Scripts' / 'pip.exe'
    requirements_path = current_dir / 'requirements.txt'
    installed_requirements_path = env_dir / 'Scripts' / 'installed_requirements.txt'

    if os.path.exists(env_dir):  # env exists so attempt to compare requirements
        # To ensure compatibility with previously installed envs, removing old envs
        if not os.path.exists(installed_requirements_path):
            shutil.rmtree(env_dir)
            time.sleep(2)
        else:
            old_req = open(installed_requirements_path).read().splitlines()
            new_req = open(requirements_path).read().splitlines()
            diff = list(set(old_req).difference(new_req))

            if diff:
                print(f'An old installation has been found and needs to be replaced.'
                      f'\nOld requirements: ----------------\n{old_req}'
                      f'\nNew requirements: ----------------\n{new_req}'
                      f'\nDifferences are: ----------------\n{diff}')

                # Remove old env folder
                shutil.rmtree(env_dir)
                time.sleep(2)

    if not os.path.exists(env_dir):
        # create a virtual environment
        try:
            env_dir.mkdir(parents=False, exist_ok=True)
        except PermissionError:
            message = f'The chosen folder is not writable. Please choose a folder where write is permitted.' \
                      f'\nCurrent folder is: {str(current_dir)}.'
            Mbox('Error', message, 0)
            sys.exit(message)

        subprocess.check_call([str(Path(sys.executable).parent / 'Scripts/virtualenv.exe'), f'{str(env_dir)}'])
        
        # copy essential python packages(python39.zip) to virtual environment
        # see https://github.com/pypa/virtualenv/issues/1185
        if not os.path.exists(env_dir/'Scripts/python39.zip'):
            copyfile(Path(sys.executable).parent / 'python39.zip', env_dir/'Scripts/python39.zip')

        # install requirements
        mess = 'Python packages will now be installed. An internet connection is needed.\n\n' \
               'You can follow the addition of the packages in the following subfolder:\n' + str(env_dir) + \
               '\\Lib\\site-packages' \
               '\nThe process will take several minutes, depending on internet speed.'

        Mbox('Starting installing python packages', mess, 0)

        subprocess.check_call(
            [str(pip_path), 'install', '-r', str(requirements_path)])
            
        # Special step for GPU enabling for CellPose
        subprocess.check_call([str(pip_path), 'uninstall', '-y', 'torch'])

        # Install GPU toolkit
        subprocess.check_call([str(pip_path), 'install', '-v', 'torch', '--extra-index-url',
                              'https://download.pytorch.org/whl/cu113'])

        # Creating a copy of requirements for further comparison if the script is run again in same folder
        if os.path.exists(installed_requirements_path):
            os.remove(installed_requirements_path)
        copyfile(requirements_path, installed_requirements_path)

    # Check if input image exists
    inputImagePath_ = params['inputImagePath']
    outputImagePath_ = params['outputImagePath']
    if not os.path.exists(inputImagePath_):
        raise ValueError('Error: {inputImagePath_} does not exist')

    # Get the path of the folder that contains this python script
    parentFolder = str(Path(__file__).parent)

    # Get the path of python executable in the virtual environment
    pythonExec_ = parentFolder + '\\env\\Scripts\\python.exe'

    # Log
    message = f'Python was installed here:\n{pythonExec_}\n\nYou can now drag & drop python recipes in Aivia.'
    Mbox('Install complete', message, 0)
    print(message)
    
    # Load image
    input_img = imread(inputImagePath_)
    
    # Dummy save
    imsave(outputImagePath_, input_img)


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    

if __name__ == '__main__':
    params = {}
    params['inputImagePath'] = 'test_8b.tif'
    params['outputImagePath'] = 'testResult.tif'

    run(params)

# CHANGELOG
# v1_10: - Removed "-v" (verbose) tag to pip install which is preventing the installation with Aivia 12.0.0.38705
# v1_11: - Added a popup to notify about end of install
# v1_12: - Error message if chosen folder is not writable.
#        - Also adding the ability to compare requirements to existing for a potential update.
