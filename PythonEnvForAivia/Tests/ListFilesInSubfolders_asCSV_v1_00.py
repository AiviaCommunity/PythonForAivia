import os
import csv
import glob
from itertools import zip_longest

fold = r'D:\PythonCode\Python_scripts\Projects\PythonEnvForAivia_A15.0_Py3.12\Recipes'

'''
Creates a csv file with each column being a subfolder.
'''

# [INPUT Name:inputImagePath Type:string DisplayName:'Any channel']
# [OUTPUT Name:resultPath Type:string DisplayName:'Dummy to delete']
def run(params):

    # Extract all subfolders
    file_list = []
    for subfold in os.listdir(fold):
        subfold_p = os.path.join(fold, subfold)
        if os.path.isdir(subfold_p):
            for file in os.listdir(subfold_p):
                if not os.path.isdir(os.path.join(subfold_p, file)):
                    file_list.append([file, subfold])

    # Writing to csv file
    out_file = os.path.join(fold, 'List of files.csv')
    with open(out_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerows(file_list)


if __name__ == '__main__':
    params = {}
    run(params)
