import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import SkeletonizeObjects
from Tests.utils.comparison import isIdentical


'''
Computes a skeleton of the input image based on the thinning of its binarization:

 1. The image is binarized (thresholded) based on the user's "Threshold" input
 2. The binarized image is thinned according to the methodology explained in
    the linked documentation
 3. (Optional) The skeleton image is closed based on the radius provided by the user.
    If the "Radius" is 0, no closing is performed.
 4. The skeleton is converted to the bit space from the original image.
 5. The skeleton is passed to Aivia's mesh creation engine to output the result as a mesh.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    ground_truth_path_2 = config.pop('groundTruthPath_2')

    result_value = SkeletonizeObjects.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultObjectPath'))
    assert isIdentical(ground_truth_path_2, config.get('resultImagePath'))

    return True

class Test_SkeletonizeObjects(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "SkeletonizeObjects", "Config_SkeletonizeObjects.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_SkeletonizeObjects_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_SkeletonizeObjects, test_name, test_method)


if __name__ == "__main__":
    unittest.main()