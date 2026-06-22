import unittest
import json
import os
import ctypes
from Recipes.TransformImages import ZColorCoding
from Tests.utils.comparison import isIdentical


'''
Uses matplotlib colormaps to retrieve colors used to create color gradients applied to individual Z planes in a 3D image.
Can be used with timepoints too, but is not adapted to 4D/5D images.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    ground_truth_path_2 = config.pop('groundTruthPath_2')
    ground_truth_path_3 = config.pop('groundTruthPath_3')

    result_value = ZColorCoding.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPathRed'))
    assert isIdentical(ground_truth_path_2, config.get('resultPathGreen'))
    assert isIdentical(ground_truth_path_3, config.get('resultPathBlue'))

    return True

class Test_ZColorCoding(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ZColorCoding", "Config_ZColorCoding.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ZColorCoding_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ZColorCoding, test_name, test_method)


if __name__ == "__main__":
    unittest.main()