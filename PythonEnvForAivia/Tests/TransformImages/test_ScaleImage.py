import unittest
import json
import os
from Recipes.TransformImages import ScaleImage
from Tests.utils.comparison import isIdentical

# NOTE: When running this test< just accept default parameters for each run on the popup window
# Don't change the parameter values in the popup window

def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    ScaleImage.run(params=config)
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    assert isIdentical(ground_truth_path.replace(".tif","-scaled.tif"), config.get("resultPath").replace(".tif","-scaled.tif"))
    return True

class Test_ScaleImage(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","ScaleImage_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ScaleImage_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ScaleImage, test_name, test_method)


if __name__ == "__main__":
    unittest.main()