# Python for Aivia

Here you will find Python recipes and helper functions for Aivia users.

The goal of this repository is to organize the work of the DRVision team and the Aivia community at large.

_Note: This is currently a work in progress, but we wanted to begin sharing it with our user community so they can use what we've created and make their own contributions._

## Repository Organization

In this main repository you will find a few different folders:

* `DRVision/Snapshots/` is for storing files necessary to build proper documentation, and can be ignored unless you are contributing to that documentation.
* `TestData/` contains images for testing recipes. See `TestData/README.md` for more information.
* `Recipes/` contains .py files that can be dragged into Aivia and used as recipes in Aivia's Analysis Tools panel. Each of these recipes is a single, self-contained piece of code that can be used independently, except in cases where the .py file has accompanying files of the same name (e.g. .ui files to describe PyQt interfaces for .py files).
* `Utilities/` contains useful companion scripts for the Aivia workflow, but that must be used in a Python interpreter separate from Aivia.

## Installation

Download and drag any file from the `Recipes/` directory into Aivia. Your recipe will show up in the Recipe Console of Aivia's Analysis Tools panel.

For debugging purposes we recommend that you navigate to File > Options > Logging in Aivia, then set the "Verbosity" to "Everything":

![Turn on the most verbose logging.](DRVisionFiles/Snapshots/LogEverything.png "Set Verbosity of Everything")

From this panel you can also click the "Open" button to see the log file. Python errors are printed here with full tracebacks to help you diagnose issues with code.

## Style Guidelines

Unless otherwise specified here, we recommend you follow [PEP 8](https://www.python.org/dev/peps/pep-0008/ "PEP 8").

Each recipe is intended for use on its own, without requiring the user to download the entire repository of recipes for it to function. Therefore, it is best practice that each recipe contains its own documentation and list of requirements.

### Naming

The name of your recipe is how it will show in the Aivia recipe console:

![Recipe name in the Aivia console.](DRVisionFiles/Snapshots/PythonFilenameInAivia.png "Recipe Naming Example")


We recommend (and may enforce) the following guidelines for file naming: 

* PascalCase with no spaces
* No versioning
* No special characters

For example, instead of naming your recipe "Track_Objects_2D+t_v02.py", name it "TrackObjects2D.py" or "TrackObjects2DandT.py".

For organizational purposes we currently recommend that if you have a multi-file structure, such as a .json containing data that your .py file depends on, you name the files the same thing except for the different extensions. This will group files together and make it obvious to users that the files go together. If you have a better suggestion for how to organize multi-file recipes, please make a documentation issue.

More importantly, it is important that your script names do not conflict with any other module names in your PATH environment variable! Uniquely name your file to avoid this conflict. For example, if you make a wrapper for a function from scikit-image, do not name the file with the same name as the file that defines the original function within scikit-image.

### Documentation

Create a docstring towards the top of your recipe file. Use this docstring to provide a description of what the module does and what your input parameters are (and preferably their expected type). See the [numpy docstring guidelines](https://numpydoc.readthedocs.io/en/latest/format.html) for inspiration.

### Dependencies

Aivia uses the Python environment that your PATH environment variable points to. Each recipe may require its own set of modules to be installed in that environment. Using a global `requirements.txt` for the entire repository may lead users to install many modules that aren't required for the given that they want to use recipe. Therefore, we recommend you include a requirements section in your recipe file's docstring to indicate which non-standard packages are required for that one recipe. For example, consider a script with the following import statements:

```python
import os
import numpy as np
from skimage.io import imread, imsave
from skimage.exposure import adjust_sigmoid, rescale_intensity
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QImage, QPixmap
```

Following the [numpy docstring guidelines](https://numpydoc.readthedocs.io/en/latest/format.html) as mentioned above, you would add a `Requirements` sections to your docstring as follows:

```python
"""
Creates a pop-up window for parameterizing a Sigmoid transform.

Requirements
------------
numpy (comes with Aivia installer)
scikit-image (comes with Aivia installer)
PyQt5

Parameters
----------
Input Image : Aivia channel
  Input channel to use for the transform.

Returns
-------
Aivia channel
  Result of the transform
"""
```
