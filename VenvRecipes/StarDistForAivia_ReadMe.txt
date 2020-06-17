
Installation
------------
1. Download the StarDist virtual environment ZIP file "StarDist_virtualEnvironment.zip" from dropbox
   https://www.dropbox.com/s/482p8iz5dt77oo8/StarDist_virtualEnvironment.zip?dl=1
2. Unzip "StarDist_virtualEnvironment.zip" to a local folder
3. The StarDist python recipe for Aivia is "\StarDist_venv\StarDist_Aivia.py"


Execution
---------
1. Load StarDist python recipe "StarDist_Aivia.py" onto Aivia
   - "StarDist_Aivia.py" is stored under the top folder "\StarDist_venv"
   - Load the recipe by using "File>Open" or drag-and-drop
2. Load target image onto Aivia
3. In Aivia analysis tools, adjust input, output, and processing parameters
3. Click on "Start" button and wait for the result


StarDist Information
--------------------
This Aivia python recipe applies the StraDist 2D or 3D deep learning model to
generate segmentation for convex shape objects in 2D or 3D images.

StarDist GitHub: https://github.com/mpicbg-csbd/stardist

The source of the pre-trained 2D and 3D StarDist Models are listed below:
(1) 2D_demo model: https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/2D_demo
(2) 2D_dsb_2018: https://github.com/mpicbg-csbd/stardist/tree/master/models/paper/2D_dsb2018
(3) 2D_fluor_nuc: https://drive.switch.ch/index.php/s/oCGZJaM949hMzjJ
    Please also check: https://github.com/mpicbg-csbd/stardist/issues/46
(4) 3D_demo model: https://github.com/mpicbg-csbd/stardist/tree/master/models/examples/3D_demo

StarDist is set up with some parameters provided by the user:
    - Model: The user chooses model to use

    - Probability Threshold:
      Confidence lower than this threshold will be removed. Higher probability
      threshold values lead to fewer segmented objects, but will likely avoid
      false positives.

    - NMS Threshold:
      NMS stands for Non-maximum suppression threshold. A higher NMS threshold
      allows segmented objects to overlap substantially. A lower NMS threshold
      suppresses the object with lower confidence.

    - Percentile Normalization:
      We provide percentile-base normalization for users.
      The default is 2.0 for percentile_low and 99.9 for percentile_high.
      If percentile_low is higher than or equal to percentile_high, the recipe
      will choose the default value.
      
	  
Requirements
------------
StarDist_venv - the StarDist python virtual environment in a folder that contains 
all required python packages to run the StarDist


Parameters
----------
Input Image : Aivia channel
    Input channel to segment.

Diameter : double
    Approximate size of the structures you wish to segment (in pixels).

Model : int
    To determine which StarDist model you wish to run.
    0 : 2D_demo
    1 : 2D_fluor_nuc
    2 : 2D_DSB
    3 : 3D_demo

Probability Threshold : double
    If an object's confidence is lower than this threshold, it will be removed.

NMS Threshold : double
    Non maximum suppression threshold

percentile_high : int
    The percentile to be normalized to 1.

percentile_low : int
    The percentile to be normalized to 0.


Returns
-------
Aivia channel
    The segmentation is output by StarDist model.