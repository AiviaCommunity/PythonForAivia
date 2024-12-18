# Test Datasets for Aivia Scripts

It makes sense to test each Aivia recipe on four distinct cases with different image dimensions:

* 2D image
* 2D image with time
* 3D image
* 3D image with time
* RGB image

When you propose to add a recipe to our repository, we recommend testing it on each of the four examples images in this `/TestData/` folder to cover each of these use cases. To keep track of your work, please feel free to create an issue or pull request with check boxes for each of these test cases. Copy/paste the following code into the issue or pull request to format this correctly:

```
- [ ] Tested in 2D
- [ ] Tested in 2D+T
- [ ] Tested in 3D
- [ ] Tested in 3D+T
```

See an example of an enhancement issue for adding a new Python recipe to the repository [here](https://github.com/AiviaCommunity/PythonForAivia/issues/3).

Note that not all scripts need to pass these tests to be added. In some cases, your script may not apply to images of certain dimensions (e.g. an "in-place maximum intensity projection" recipe only makes sense in 3D). This is OK! Please explain which cases are not applicable, and preferably use a try/catch or if/else structure to report these issues to the user in the Aivia log.

# Running Tests

To execute unittests on Windows, open Terminal/Powershell and navigate into the [`PythonEnvForAivia`](./) folder. Make sure you have already set up the python environment using [`FirstTimeSetup.py`](../FirstTimeSetup.py). See [`PythonEnvForAivia/README.md#installation`](../README.md#installation) for more details.


To run all tests, run the command:
```python
python -m unittest discover .
```

To run tests on the folders of recipes (for example, all recipes under [`ProcessImages`](../Recipes/ProcessImages/)), run the command:
```python
python -m unittest discover Tests\ProcessImages
```

To run specific tests (for example, [`AdjustGamma.py`](../Recipes/ProcessImages/AdjustGamma.py)), run the command:
```python
python -m unittest Tests.ProcessImages.test_AdjustGamma
```

Running tests will result in each recipe's respective output to be saved to a folder called `GroundTruth/RECIPE_NAME/outputs/`, which is then cross referenced against `GroundTruth/RECIPE_NAME/ground_truth/`

# Test Directory Structure

## List of helper directories
- [InputTestImages](../Tests/InputTestImages/): All input images for tests are stored here
- [utils](../Tests/utils/): Common functions shared across all tests are stored here.


Tests mimic the folder structure of [`Recipes`](../Recipes/). Each family (directory) of recipes has the following structure (an example for `AdjustGamma.py` is provided below:
```
ProcessImages
├── GroundTruths                       # Contains ground truth images and outputs
│   │                                  #        of  ALL unit tests
│   ├── AdjustGamma                    # Contains ground truth images and outputs
│   │   │                              #        of  only AdjustGamma unit tests
│   │   ├── ground_truth               #
│   │   └── outputs                    #
│   └── ...
├── TestConfigs                        # Contains all .json configuration files for all tests
│                                      #        The json config for AdjustGamma is titled:
│                                      #        AdjustGamma_configs.json.
│                                      #        All Configs have the suffix "_configs.json."
└── test_AdjustGamma.py                # Unit tests for AdjustGamma recipe
```

# Tests Performed

![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png) indicates that an active unit test has been implemented for a given recipe, and that recipe is compatible with the given image format.

![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png) indicates that the given recipe does not have a unit test for the given image format, but is compatible with the image format

Parent Directory | Recipe Name | 2D | 2D +T | 3D | 3D+T | RGB
-|-|-|-|-|-|-
[ProcessImages](../Recipes/ProcessImages)| [`AdjustGamma.py`](../Recipes/ProcessImages/AdjustGamma.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	
[ProcessImages](../Recipes/ProcessImages)| [`AdjustGamma_MagicGui.py`](../Recipes/ProcessImages/AdjustGamma_MagicGui.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	
[ProcessImages](../Recipes/ProcessImages)| [`AdjustSigmoid.py`](../Recipes/ProcessImages/AdjustSigmoid.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	
[ProcessImages](../Recipes/ProcessImages)| [`DrawArrayOfShapes_2D.py`](../Recipes/ProcessImages/DrawArrayOfShapes_2D.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`DrawShapes_2D.py`](../Recipes/ProcessImages/DrawShapes_2D.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`DrawShollCircles_2D_AiviaGui.py`](../Recipes/ProcessImages/DrawShollCircles_2D_AiviaGui.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`MeijeringNeuriteness.py`](../Recipes/ProcessImages/MeijeringNeuriteness.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)
[ProcessImages](../Recipes/ProcessImages)| [`MorphologicalTexture.py`](../Recipes/ProcessImages/MorphologicalTexture.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`ShapeIndex.py`](../Recipes/ProcessImages/ShapeIndex.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`Skeletonize.py`](../Recipes/ProcessImages/Skeletonize.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`SkeletonizeObjects.py`](../Recipes/ProcessImages/SkeletonizeObjects.py)|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		
[ProcessImages](../Recipes/ProcessImages)| [`SplitLabeledMask.py`](../Recipes/ProcessImages/SplitLabeledMask.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		
[ProcessImages](../Recipes/ProcessImages)| [`SuperpixelPainter.py`](../Recipes/ProcessImages/SuperpixelPainter.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`ThresholdWithoutBorders2D.py`](../Recipes/ProcessImages/ThresholdWithoutBorders2D.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		
[ProcessImages](../Recipes/ProcessImages)| [`ThresholdWithoutBorders3D.py`](../Recipes/ProcessImages/ThresholdWithoutBorders3D.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		
[TransformImages](../Recipes/TransformImages)| [`MaxIntensityProjection.py`](../Recipes/TransformImages/MaxIntensityProjection.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`MaxIntensityProjectionRGB.py`](../Recipes/TransformImages/MaxIntensityProjectionRGB.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`MaxMask.py`](../Recipes/TransformImages/MaxMask.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[TransformImages](../Recipes/TransformImages)| [`MaxSlices.py`](../Recipes/TransformImages/MaxSlices.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[TransformImages](../Recipes/TransformImages)| [`MinSlices.py`](../Recipes/TransformImages/MinSlices.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[TransformImages](../Recipes/TransformImages)| [`RGBtoLuminance.py`](../Recipes/TransformImages/RGBtoLuminance.py)|		|		|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)
[TransformImages](../Recipes/TransformImages)| [`Rotate2D.py`](../Recipes/TransformImages/Rotate2D.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|		|	
[TransformImages](../Recipes/TransformImages)| [`Rotate3D_90deg.py`](../Recipes/TransformImages/Rotate3D_90deg.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	
[TransformImages](../Recipes/TransformImages)| [`ScaleImage.py`](../Recipes/TransformImages/ScaleImage.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[TransformImages](../Recipes/TransformImages)| [`ScaleImage_ForStarDist.py`](../Recipes/TransformImages/ScaleImage_ForStarDist.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[TransformImages](../Recipes/TransformImages)| [`StackReg_ImageAlignment.py`](../Recipes/TransformImages/StackReg_ImageAlignment.py)|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|		|	
[TransformImages](../Recipes/TransformImages)| [`ZColorCoding.py`](../Recipes/TransformImages/ZColorCoding.py)|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`AiviaExperimentCreator.py`](../Recipes/ConvertImagesForAivia/AiviaExperimentCreator.py)|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`DICOMStackToTIFF.py`](../Recipes/ConvertImagesForAivia/DICOMStackToTIFF.py)|		|		|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|		|	
[ConvertImagesForAivia](../Recipes/ConvertImagesForAivia)| [`MultiWellPlateConverter_OperaPhenix.py`](../Recipes/ConvertImagesForAivia/MultiWellPlateConverter_OperaPhenix.py)|		|		|		|		|	
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`CalculateIntersectionOverUnion.py`](../Recipes/CollectImageMetrics/CalculateIntersectionOverUnion.py)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`ImageComparisonMetrics.py`](../Recipes/CollectImageMetrics/ImageComparisonMetrics.py)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)	|	![#c5f015](https://placehold.co/15x15/c5f015/c5f015.png)
[CollectImageMetrics](../Recipes/CollectImageMetrics)| [`ReadTiffTags.py`](../Recipes/CollectImageMetrics/ReadTiffTags.py)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)	|	![#f03c15](https://placehold.co/15x15/f03c15/f03c15.png)

