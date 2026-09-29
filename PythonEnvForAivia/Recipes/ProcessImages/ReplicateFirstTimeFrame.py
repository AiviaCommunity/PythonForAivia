import numpy as np
from skimage.io import imread, imsave
import sys
import subprocess

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
    if zCount == 1 and tCount == 1:
        error_mess = f'Error: detected dimensions do not contain time or Z. (t={tCount}, z={zCount})'
        if not params.get('debugMode', False):
            Mbox(error_mess, 'Error', 0)
        sys.exit(error_mess)

    # Reading channel (expected (T), (Z), Y, X)
    input_data = imread(inputImagePath_)

    # Reshaping to ensure TZYX shape
    reshaped_data = input_data
    if tCount == 1:
        reshaped_data = np.expand_dims(input_data, axis=0)
    if zCount == 1:
        reshaped_data = np.expand_dims(input_data, axis=1)

    output_data = np.zeros_like(reshaped_data)

    # Copying data of first frame
    for t in range(tCount):
        for z in range(zCount):
            # 3D+T
            if tCount > 1 and zCount > 1:
                output_data[t, z, ...] = reshaped_data[0, z, ...]
            else:
                output_data[t, z, ...] = reshaped_data[0, 0, ...]

    imsave(outputImagePath_, output_data)


def Mbox(title, text, style):
    style_tags = ["OkOnly", "OkCancel", "YesNo", "YesNoCancel"]
    cmd = [
        "powershell",
        "-Command",
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"$x=[Microsoft.VisualBasic.Interaction]::MsgBox('{text}', "
        f"[Microsoft.VisualBasic.MsgBoxStyle]::{style_tags[style]}, '{title}');"
        "Write-Output $x"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return result.stdout.strip()        # return = "Ok" or "Cancel"
    except:
        return None


if __name__ == '__main__':
    fold = r'D:\PythonCode\_tests'
    params = {'inputImagePath': rf'{fold}\XYT_160x160x16_1ch_8bit_nuclei-fluo_embryo_APP-2Dalign_IJ1.53t.tif',
              'outputImagePath': rf'{fold}\output.tif',
              'ZCount': 1, 'TCount': 16, 'debugMode': True}

    run(params)

# CHANGELOG 
#   v1.10: - Now compatible for Z or T
#   v1_20: - Mbox with VB for Aivia 16
#   v1_30: - Bug with TZYX data: was replicating Z and T. Now only T with these dimensions
