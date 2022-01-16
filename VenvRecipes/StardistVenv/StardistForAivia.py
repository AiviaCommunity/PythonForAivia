import os.path
import subprocess
import pathlib
from shutil import copyfile
from pathlib import Path
import sys

"""
This Aivia python recipe invokes the subprocess to execute StarDist_venv.py
under the required virtual environment. During the first execution, it will
create the required virtual environment.
"""


# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [INPUT Name:outputType Type:int DisplayName:'Output(0:Lb,1:Msk)' Default:0 Min:0 Max:1]
# [INPUT Name:modelSelection Type:int DisplayName:'Model(0:demo,1:fluor, 2:DSB,3:3D)' Default:0 Min:0 Max:4]
# [INPUT Name:probThreshold Type:double DisplayName:'Probability Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:nmsThreshold Type:double DisplayName:'NMS Threshold (0.0-1.0)' Default:0.5 Min:0.0 Max:1.0]
# [INPUT Name:normalizationLow Type:double DisplayName:'Percentile Normalization Low (0.0-100.0)' Default:2.0 Min:0.0 Max:100.0]
# [INPUT Name:normalizationHigh Type:double DisplayName:'Percentile Normalization High (0.0-100.0)' Default:99.9 Min:0.0 Max:100.0]
# [OUTPUT Name:resultPath Type:string DisplayName:'Segmentation Result']
def run(params):

    env_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / 'env'

    if not os.path.exists(env_dir):
        env_dir.mkdir(parents=False, exist_ok=True)
        subprocess.check_call([str(Path(sys.executable).parent / 'Scripts/virtualenv.exe'), f'{env_dir}'])

    # copy essential python packages(python39.zip) to virtual environment
    # see https://github.com/pypa/virtualenv/issues/1185
    if not os.path.exists(env_dir/'Scripts/python39.zip'):
        copyfile(Path(sys.executable).parent / 'python39.zip', env_dir/'Scripts/python39.zip')

    # install requirements
    pip_path = env_dir / 'Scripts' / 'pip.exe'
    requirement_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    subprocess.check_call(
        [str(pip_path), 'install', '-r', str(requirement_dir/'requirements.txt')])
    subprocess.check_call([str(pip_path), 'install', 'stardist==0.7.3'])

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
    scrptPath_ = parentFolder + '\\Data\\StarDist_venv.py'

    # Get input, output, and parameters as strings
    zCount_ = str(z_count)
    tCount_ = str(t_count)
    model_selection_ = params['modelSelection']
    probThreshold_ = params['probThreshold']
    nmsThreshold_ = params['nmsThreshold']
    resultPath_ = params['resultPath']
    nmsThreshold_ = params['nmsThreshold']
    normalizationLow_ = params['normalizationLow']
    normalizationHigh_ = params['normalizationHigh']
    outputType_ = params['outputType']
    resultPath_ = params['resultPath']

    # Display input, output, and parameters
    print('------------------------------------------')
    print('         StarDist Python Recipe')
    print('------------------------------------------')
    print(f'       pythonExec_= {pythonExec_}')
    print(f'        scrptPath_= {scrptPath_}')
    print(f'   inputImagePath_= {inputImagePath_}')
    print(f'           zCount_= {zCount_}')
    print(f'           tCount_= {tCount_}')
    print(f'  model_selection_= {model_selection_}')
    print(f'    probThreshold_= {probThreshold_}')
    print(f'     nmsThreshold_= {nmsThreshold_}')
    print(f' normalizationLow_= {normalizationLow_}')
    print(f'normalizationHigh_= {normalizationHigh_}')
    print(f'       outputType_= {outputType_}')
    print(f'       resultPath_= {resultPath_}')
    print('------------------------------------------')

    # Run the script under the virtual environment
    proc = subprocess.Popen(
        [pythonExec_, scrptPath_, inputImagePath_, zCount_, tCount_,
         model_selection_, probThreshold_, nmsThreshold_,
         normalizationLow_, normalizationHigh_, outputType_, resultPath_],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Write sub process outputs
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
