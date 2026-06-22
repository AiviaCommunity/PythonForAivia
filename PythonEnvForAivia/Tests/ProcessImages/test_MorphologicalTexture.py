import unittest
import json
import os
from Recipes.ProcessImages import MorphologicalTexture
from Tests.utils.comparison import isIdentical


'''
Estimates image texure using morphological transforms.
Closing and opening operations are performed in parallel. A disk kernel
is used for 2D images, and a ball kernel is used for 3D images. The user
defines the size of these kernels.
The closing returns the max value within that neighborhood for every
voxel, resulting in a brighter image.
The opening returns the min value within that neighborhood for every
voxel, resulting in a darker image.
The opening result is then subtracted from the closing result to create
the final output.'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = MorphologicalTexture.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_MorphologicalTexture(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "MorphologicalTexture", "Config_MorphologicalTexture.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_MorphologicalTexture_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_MorphologicalTexture, test_name, test_method)


if __name__ == "__main__":
    unittest.main()