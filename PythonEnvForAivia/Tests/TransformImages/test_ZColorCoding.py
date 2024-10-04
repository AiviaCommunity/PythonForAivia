import unittest
import json
import os
from Recipes.TransformImages import ZColorCoding
from Tests.utils.comparison import isIdentical

# NOTE: When running this test< just accept default parameters for each run on the popup window
# Don't change the parameter values in the popup window

def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    ZColorCoding.run(params=config)
    groundtruth_red = ground_truth_path.replace(".tif","_red.tif")
    groundtruth_green = ground_truth_path.replace(".tif","_green.tif")
    groundtruth_blue = ground_truth_path.replace(".tif","_blue.tif")
    
    assert isIdentical(groundtruth_red, config.get("resultPathRed"))
    assert isIdentical(groundtruth_green, config.get("resultPathGreen"))
    assert isIdentical(groundtruth_blue, config.get("resultPathBlue"))
    return True

class Test_ZColorCoding(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","ZColorCoding_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ZColorCoding_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ZColorCoding, test_name, test_method)


if __name__ == "__main__":
    unittest.main()