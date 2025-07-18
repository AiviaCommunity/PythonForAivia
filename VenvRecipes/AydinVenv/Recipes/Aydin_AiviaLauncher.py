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

import aydin.gui.gui as agui

"""
See: https://royerlab.github.io/aydin/v0.1.15/tutorials/gui_tutorials.html

Requirements
------------
Aivia 11.0 to 14.1

Parameters
----------
Input Image : Aivia channel
    any channel

Returns
-------
Nothing. An error shows up when GUI is closed, ignore it...

"""

# [INPUT Name:inputImagePath Type:string DisplayName:'Input Image']
# [OUTPUT Name:resultPath Type:string DisplayName:'to delete']
def run(params):
    agui.run('ver')


if __name__ == '__main__':
    params = {}    
    run(params)

