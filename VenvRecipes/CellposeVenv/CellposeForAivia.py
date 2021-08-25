import os.path
import subprocess
import pathlib
from pathlib import Path
from shutil import copyfile
import virtualenv
import sys

"""
This Aivia python recipe invokes the subprocess to execute Cellpose_venv.py
under the required virtual environment. During the first execution, it will
create the required virtual environment.
"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:diameter Type:double DisplayName:'Diameter (px)' Default:30.0 Min:0.0 Max:1000.0]
# [INPUT Name:modelType Type:int DisplayName:'Model Type (0=cyto, 1=nuc)' Default:0 Min:0 Max:1]
# [INPUT Name:cellThreshold Type:double DisplayName:'Cell Threshold' Default:0.0 Min:0.0 Max:6.0]
# [INPUT Name:flowThreshold Type:double DisplayName:'Flow Threshold' Default:0.4 Min:0.0 Max:1.0]
# [OUTPUT Name:confMapPath Type:string DisplayName:'Confidence Map']
# [OUTPUT Name:maskPath Type:string DisplayName:'Mask']
def run(params):

    env_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'env'

    if not os.path.exists(env_dir):
        # create a virtual environment
        env_dir.mkdir(parents=False, exist_ok=True)
        subprocess.check_call([str(Path(sys.executable).parent / 'Scripts/virtualenv.exe'), f'{env_dir}'])

    # copy essential python packages(python36.zip) to virtual environment
    # see https://github.com/pypa/virtualenv/issues/1185
    if not os.path.exists(env_dir/'Scripts/python36.zip'):
        copyfile(Path(sys.executable).parent / 'python36.zip', env_dir/'Scripts/python36.zip')

    # install requirements
    pip_path = env_dir / 'Scripts' / 'pip.exe'
    requirement_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    subprocess.check_call(
        [str(pip_path), 'install', '-r', str(requirement_dir/'requirements.txt')])

    # Check if input image exists
    inputImagePath_ = params['inputImagePath']
    if not os.path.exists(inputImagePath_):
        raise ValueError('Error: {inputImagePath_} does not exist')

    # Get Z count and T count
    z_count, t_count = [int(params[f'{s}Count']) for s in ['Z', 'T']]

    # Get the path of the folder that contains this python script
    parentFolder = str(Path(__file__).parent)

    # Get the path of python executable in the virtual environment
    pythonExec_ = parentFolder + '\\env\\Scripts\\python.exe'

    # Get the path of the python script to run under the virtual environment
    scrptPath_ = parentFolder + '\\Data\\Cellpose_venv.py'

    # Get input, output, and parameters as strings
    zCount_ = str(z_count)
    tCount_ = str(t_count)
    diameter_ = params['diameter']
    model_type_ = params['modelType']
    conf_map_path_ = params['confMapPath']
    mask_path_ = params['maskPath']
    cellprob_threshold_ = params['cellThreshold']
    flow_threshold_ = params['flowThreshold']

    # Display input, output, and parameters
    print('------------------------------------------')
    print('         Cellpose Python Recipe')
    print('------------------------------------------')
    print(f'        pythonExec_= {pythonExec_}')
    print(f'         scrptPath_= {scrptPath_}')
    print(f'    inputImagePath_= {inputImagePath_}')
    print(f'            zCount_= {zCount_}')
    print(f'            tCount_= {tCount_}')
    print(f'          diameter_= {diameter_}')
    print(f'        model_type_= {model_type_}')
    print(f'     conf_map_path_= {conf_map_path_}')
    print(f'         mask_path_= {mask_path_}')
    print(f'cellprob_threshold_= {cellprob_threshold_}')
    print(f'    flow_threshold_= {flow_threshold_}')
    print('------------------------------------------')

    # Run the script under the virtual environment
    proc = subprocess.Popen(
                [pythonExec_, scrptPath_, inputImagePath_, zCount_, tCount_,
                 diameter_, model_type_, conf_map_path_, mask_path_,
                 cellprob_threshold_, flow_threshold_],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)

    # Write sub process outputs
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
