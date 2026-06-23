import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import ThresholdWithoutBorders2D
from Tests.utils.comparison import isIdentical


'''
Thresholds an image for segmentation, then clears any objects intersecting the image borders before
creating an object set in Aivia.
This recipe only works in 2D. Use ThresholdWithoutBorders3D instead for 3D cases.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = ThresholdWithoutBorders2D.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultObjectPath'))

    return True

class Test_ThresholdWithoutBorders2D(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ThresholdWithoutBorders2D", "Config_ThresholdWithoutBorders2D.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ThresholdWithoutBorders2D_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ThresholdWithoutBorders2D, test_name, test_method)


if __name__ == "__main__":
    unittest.main()