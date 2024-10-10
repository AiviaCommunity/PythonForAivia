# Python for Aivia

Here you will find Python recipes and helper functions for Aivia users.
The goal of this repository is to organize the work of the Aivia team and the Aivia community at large.

# Table of Contents

* [Recipe Directory](#recipe-directory)
* [Repository Organization](#repository-organization)
* [Installation](#installation)
* [Templates](#templates)
* [Style Guidelines](#style-guidelines)
    * [Naming](#naming)
    * [Documentation](#documentation)
    * [Dependencies](#dependencies)
    * [Periodic file cleaning](#periodic-file-cleaning)
    * [Version-dependent notes](#version-dependent-notes)

## Recipe Directory [^](#table-of-contents)

Below is a table of implemented recipes and their image format compatibility

Parent Directory | Recipe Name | 2D | 2D +T | 3D | 3D+T | RGB
-|-|-|-|-|-|-
[ProcessImages](../Recipes/ProcessImages)| [`AdjustGamma.py`](../Recipes/ProcessImages/AdjustGamma.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	
[ProcessImages](../Recipes/ProcessImages)| [`AdjustGamma_MagicGui.py`](../Recipes/ProcessImages/AdjustGamma_MagicGui.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	
[ProcessImages](../Recipes/ProcessImages)| [`AdjustSigmoid.py`](../Recipes/ProcessImages/AdjustSigmoid.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	
[ProcessImages](../Recipes/ProcessImages)| [`DrawArrayOfShapes_2D.py`](../Recipes/ProcessImages/DrawArrayOfShapes_2D.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`DrawShapes_2D.py`](../Recipes/ProcessImages/DrawShapes_2D.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`DrawShollCircles_2D_AiviaGui.py`](../Recipes/ProcessImages/DrawShollCircles_2D_AiviaGui.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`MeijeringNeuriteness.py`](../Recipes/ProcessImages/MeijeringNeuriteness.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)
[ProcessImages](../Recipes/ProcessImages)| [`MorphologicalTexture.py`](../Recipes/ProcessImages/MorphologicalTexture.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`ShapeIndex.py`](../Recipes/ProcessImages/ShapeIndex.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`Skeletonize.py`](../Recipes/ProcessImages/Skeletonize.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`SkeletonizeObjects.py`](../Recipes/ProcessImages/SkeletonizeObjects.py)|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`SplitLabeledMask.py`](../Recipes/ProcessImages/SplitLabeledMask.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		
[ProcessImages](../Recipes/ProcessImages)| [`SuperpixelPainter.py`](../Recipes/ProcessImages/SuperpixelPainter.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`ThresholdWithoutBorders2D.py`](../Recipes/ProcessImages/ThresholdWithoutBorders2D.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`ThresholdWithoutBorders3D.py`](../Recipes/ProcessImages/ThresholdWithoutBorders3D.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		
[TransformImages](../Recipes/TransformImages)| [`MaxIntensityProjection.py`](../Recipes/TransformImages/MaxIntensityProjection.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`MaxIntensityProjectionRGB.py`](../Recipes/TransformImages/MaxIntensityProjectionRGB.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`MaxMask.py`](../Recipes/TransformImages/MaxMask.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[TransformImages](../Recipes/TransformImages)| [`MaxSlices.py`](../Recipes/TransformImages/MaxSlices.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[TransformImages](../Recipes/TransformImages)| [`MinSlices.py`](../Recipes/TransformImages/MinSlices.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[TransformImages](../Recipes/TransformImages)| [`RGBtoLuminance.py`](../Recipes/TransformImages/RGBtoLuminance.py)|		|		|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)
[TransformImages](../Recipes/TransformImages)| [`Rotate2D.py`](../Recipes/TransformImages/Rotate2D.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|		|	
[TransformImages](../Recipes/TransformImages)| [`Rotate3D_90deg.py`](../Recipes/TransformImages/Rotate3D_90deg.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`ScaleImage.py`](../Recipes/TransformImages/ScaleImage.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[TransformImages](../Recipes/TransformImages)| [`ScaleImage_ForStarDist.py`](../Recipes/TransformImages/ScaleImage_ForStarDist.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[TransformImages](../Recipes/TransformImages)| [`StackReg_ImageAlignment.py`](../Recipes/TransformImages/StackReg_ImageAlignment.py)|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|		|	
[TransformImages](../Recipes/TransformImages)| [`ZColorCoding.py`](../Recipes/TransformImages/ZColorCoding.py)|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`AiviaExperimentCreator.py`](../Recipes/ConvertImagesForAivia/AiviaExperimentCreator.py)|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`DICOMStackToTIFF.py`](../Recipes/ConvertImagesForAivia/DICOMStackToTIFF.py)|		|		|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|		|	
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`MultiWellPlateConverter_OperaPhenix.py`](../Recipes/ConvertImagesForAivia/MultiWellPlateConverter_OperaPhenix.py)|		|		|		|		|	
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`CalculateIntersectionOverUnion.py`](../Recipes/CollectImageMetrics/CalculateIntersectionOverUnion.py)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`ImageComparisonMetrics.py`](../Recipes/CollectImageMetrics/ImageComparisonMetrics.py)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`ReadTiffTags.py`](../Recipes/CollectImageMetrics/ReadTiffTags.py)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)	|	![#1589F0](https://placehold.co/15x15/1589F0/1589F0.png)



## Repository Organization [^](#table-of-contents)

In this main repository you will find a few different folders:

* [`PythonVenvForAivia/`](PythonVenvForAivia/) contains a virtual environment auto-builder. This is useful for users who do not know how to set a virtual environment and want to use recipes in Aivia without using any command line.
    * [`Recipes/`](PythonVenvForAivia/Recipes/) contains .py files that can be dragged into Aivia and used as recipes in Aivia's Analysis Tools panel. Each of these recipes is a single, self-contained piece of code that can be used independently, except in cases where the .py file has accompanying files of the same name (e.g. .ui files to describe PyQt interfaces for .py files).
    * [`Tests/`](PythonVenvForAivia/Tests/) contains testing scripts for recipes and test images for testing recipes. See [`README.md`](PythonEnvForAivia/Tests/README.md) for more information on its subdirectory structure.

* [`VenvRecipes/`](VenvRecipes/) contains VenvRecipe folders. Each of these folders include a .py recipe and data. Each of these recipes is also ready-to-use except they will create required virtual environment and execute under the environment automatically. To use these recipes, please download the whole subfolder of that recipe.
* [`Screenshots/`](Screenshots/) is for storing files necessary to build proper documentation, and can be ignored unless you are contributing to that documentation.

## Installation [^](#table-of-contents)

Download and drag any file from the [`PythonVenvForAivia/Recipes/`](PythonVenvForAivia/Recipes/) directory into Aivia. Your recipe will show up in the Recipe Console of Aivia's Analysis Tools panel.

For debugging purposes we recommend that you navigate to File > Options > Logging in Aivia, then set the "Verbosity" to "Everything":

![Turn on the most verbose logging.](Screenshots/LogEverything.png "Set Verbosity of Everything")

From this panel you can also click the "Open" button to see the log file. Python errors are printed here with full tracebacks to help you diagnose issues with code.

## Templates [^](#table-of-contents)

The creation of a global template is somewhat hindered by how arrays of different dimensions are handled differently by each image processing function. For now, AdjustGamma.py is the simplest example of an Aivia recipe that can be used as a template. For a more complex recipe with proper handling of all image properties encountered in Aivia (8bit, 16bit,  2D, 3D, 2D+T, 3D+T), see ShapeIndex.py.

## Style Guidelines [^](#table-of-contents)

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

Aivia uses the Python environment specified in File > Options > Advanced > Python executable. Each recipe may require its own set of modules so please check the specified requirements within the scripts if you want to use a recipe. A virtual environment auto-builder (see PythonEnvForAivia folder) is offered to users who do not want to handle the dependencies for the existing recipes. If you designed a script, please specify your requirements within the docstring paragraph. For example, consider a script with the following import statements:

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

### Periodic file cleaning
The simple bridge created between Aivia and python uses temporary files placed in the following location: 

`"C:\Users\_{windows-username}_\AppData\Local\Temp"`

Temporary ".tif" files (named `tmp*.tif`) can stay in this folder if there is an interruption in the python script.
Hence, it can be interesting to clean this folder periodically.


### Version-dependent notes

For **Aivia 11.0.x** or more, a simple-to-install environment has been created for Aivia.
* Click on the folder named "PythonVenvForAivia" and follow instructions


For Aivia 10.5.x or more, you can install non-standard packages from Aivia:
* Open Aivia and go to menu Analysis > Deep Learning Processor (or Batch and Cloud Processor) > File > Add Python Module


For Aivia 10.1.x with embedded python, the guide to install non-standard packages:
* Open terminal
* Change directory: cd "path/to/Aivia/Python/directory/" (For e.g. C:\Program Files\Leica Microsystems\Aivia 10.5.0\Python)
* Run: python -m pip install <name_of_the_module>
