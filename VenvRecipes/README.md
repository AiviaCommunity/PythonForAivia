# VenvRecipes for Aivia

After Aivia 10 update, you will need to set up a full python path to make VenvRecipes works. You will only need to do the following steps for the first time:

1. Make sure you have installed a full Python >=3.6

2. Open Aivia and go to File -> Options -> Advance -> Python executable.

3. Change the embedded Python executable to the full Python installed on your PC. For example: `C:\Program Files\Python36\python.exe`

4. Drag and drop the recipes into Aivia and run the recipes with any images.

5. Change the Python executable back to embedded Python in Aivia. The path may looks like `C:\Program Files\Leica Microsystems\Aivia 10.0.0\Python\python.exe`

VenvRecipes will be executed under the required virtual environment automatically.

Each of these recipes will create the required virtual environment for itself at the first time of execution.

## How to download VenvRecipes

1. Please download the whole folder of the recipe that you want to use. Since GitHub does not support subfolder download, we put zipped folders here for you: [ZippedVenvFolders](ZippedVenvFolders).

2. Find the `README.md` file in the subfolder to see the details of each recipe.

## VenvRecipes List

Segmentation:

1. [CellposeVenv](./CellposeVenv)
2. [StarDistVenv](./StardistVenv)
