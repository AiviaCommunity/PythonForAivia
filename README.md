# PythonForAivia

Here you will find Python recipes and helper functions for Aivia users.

The goal of this repository is to organize the work of the DRVision team and the Aivia community at large.

_Note that this currently a work in progress, but we wanted to begin sharing it with our user community so they can use what we've created and make their own contributions._

## Installation

How to get Aivia scripts onto your computer for use.

## Organization

How the folders are organized.

## Style Guidelines

Unless otherwise specified here, we recommend you follow [PEP 8](https://www.python.org/dev/peps/pep-0008/ "PEP 8").

Each recipe is intended for use on its own, without requiring the user to download the entire repository of recipes for it to function. Therefore, it is best practice that each recipe contains its own documentation and list of requirements.

### Naming

The name of your recipe is how it will show in the Aivia recipe console. We recommend (and may enfore) the following guidelines for file naming: 

* CamelCase with no spaces
* No versioning
* No special characters

For example, instead of naming your recipe "Track_Objects_2D+t_v02.py", name it "TrackObjects2D.py" or "TrackObjects2DandT.py".

More importantly, it is important that your script names do not conflict with any other module names in your PATH environment variable! Uniquely name your file to avoid this conflict. For example, if you make a wrapper for a function from scikit-image, do not name the file with the same name as the file that defines the original function within scikit-image.

### Documentation

Create a docstring towards the top of your recipe file. Use this docstring to provide a description of what the module does and what your input parameters are (and preferably their expected type). See the [numpy docstring guidelines](https://numpydoc.readthedocs.io/en/latest/format.html) for inspiration.

### Dependencies

Aivia uses the Python environment that your PATH environment variable points to. Each recipe may require its own set of modules to be installed in that environment. Using a global `requirements.txt` for the entire repository may lead users to install many modules that aren't required for the given that they want to use recipe. Therefore, we recommend you include a requirements section in your recipe file's docstring to indicate which packages are required for that one recipe. For example, consider a script with the following import statements:

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
numpy
scikit-image
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
