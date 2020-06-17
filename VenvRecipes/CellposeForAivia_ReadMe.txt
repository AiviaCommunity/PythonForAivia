
Installation
------------
1. Download the Cellpose virtual environment ZIP file "Cellpose_virtualEnvironment.zip" from dropbox
   https://www.dropbox.com/s/0dczdliehhqj0wr/Cellpose_virtualEnvironment.zip?dl=1
2. Unzip "Cellpose_venv.zip" to a local folder
3. The Cellpose python recipe for Aivia is "\Cellpose_venv\Cellpose_Aivia.py"


Execution
---------
1. Load Cellpose python recipe "Cellpose_Aivia.py" onto Aivia
   - "Cellpose_Aivia.py" is stored under the top folder "\Cellpose_venv"
   - Load the recipe by using "File>Open" or drag-and-drop
2. Load target image onto Aivia
3. In Aivia analysis tools, adjust input, output, and processing parameters
3. Click on "Start" button and wait for the result


Cellpose Information
--------------------
This Aivia python recipe applies the the Cellpose deep learning model to
generate segmentation for cells/nucleus in 2D or 3D images.

Sources of the pre-trained cellpose models are listed below:
    Cellpose Website: http://www.cellpose.org/
    Cellpsoe GitHub: https://github.com/MouseLand/cellpose
    Cellpose ducumentation: http://www.cellpose.org/static/docs/index.html
    Cellpsoe paper: https://www.biorxiv.org/content/10.1101/2020.02.02.931238v1

Cellpose is set up with some parameters provided by the user:
    - Model: the user chooses whether to use the cytoplasm or nuclei model
    - Diameter: the user provides an approximation of object size
	
	
Requirements
------------
Cellpose_venv - the Cellpose python virtual environment in a folder that contains 
all required python packages to run the Cellpose


Parameters
----------
Input Image : Aivia channel
    Input channel to segment.

Diameter : double
    Approximate size of the structures you wish to segment (in pixels).

Model : int (bool)
    Boolean to determine which Cellpose model you wish to run.
    0 : Choose the cytoplasm model (segment the whole cell).
    1 : Choose the nuclei model


Returns
-------
Confidence Map : Aivia channel
    The flow that is output by Cellpose. This represents a confidence that each voxel
    belongs to the segmentation.

Mask : Aivia channel
    Segmented result