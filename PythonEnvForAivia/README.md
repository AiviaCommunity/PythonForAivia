# Python Virtual Environment for Aivia

## General Information

The [`FirstTimeSetup.py`](/PythonEnvForAivia/FirstTimeSetup.py) script will ensure a virtual environment is created to run the python recipes for Aivia with the appropriate packages.
No further install should be needed. Hence, the script is run once only.

The recipes are then containing some code to:
- Check the existence of the virtual environment,
- Automatically activate the virtual environment to be able to run with the appropriate packages,
- Fallback on main Aivia environment which we do not recommend to modify (i.e. add new packages).


## Requirements

* Python 3.12 - comes with Aivia
* Accept the risks that come from running Python Scripts you download from the internet. These scripts are provided to you to use at your own risk. 

## Installation

1. Download the latest `PythonEnvForAivia` zip available in the releases:
   https://github.com/AiviaCommunity/PythonForAivia/releases

2. Unzip the downloaded folder `PythonEnvForAivia` in a location where there are no admin access restrictions. 
The tree structure of the folder is as follow

```bash=
  PythonEnvForAivia
  ├───FirstTimeSetup.py
  ├───requirements.txt
  ├───README.md
  └───Recipes
      └───[category subfolders]
          └───... .py

```

## Execution

1. Load [`FirstTimeSetup.py`](/PythonEnvForAivia/FirstTimeSetup.py) in Aivia by "File>Open" or drag-and-drop
2. Load any 2D image in Aivia
3. Click on "Start" button and wait for "Process Completed" message at the bottom of the recipe console
    1. Please make sure that you have the Internet connection and wait if bandwidth is slow.

## Returns

* Original image with text on top, showing what is the location of the python script that will be used

