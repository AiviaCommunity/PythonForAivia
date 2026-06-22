import unittest
import json
import os
from Recipes.TransformImages import ScaleImage
from Tests.utils.comparison import isIdentical


'''
Scales the input channel up or down (isotropic factor). Option for interpolation is in the code.
Works only for 2D/3D rescaling (not timelapses) but can be applied on a per timepoint basis.
Works for single channels.
Output path is given with "params" for test and hardcoded for regular run in Aivia'''


def run_test(config):
	ground_truth_path_2 = config.pop('groundTruthPath_2')
	file_output_value_2 = config.get('fileOutputPath_2')

    result_value = ScaleImage.run(params=config)
    
	assert isIdentical(ground_truth_path_2, file_output_value_2)

    return True

class Test_ScaleImage(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ScaleImage", "Config_ScaleImage.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ScaleImage_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ScaleImage, test_name, test_method)


if __name__ == "__main__":
    unittest.main()