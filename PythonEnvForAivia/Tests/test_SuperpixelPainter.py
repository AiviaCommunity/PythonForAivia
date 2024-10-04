import unittest
import json
import os
from Recipes.ProcessImages import SuperpixelPainter
from Tests.utils.comparison import isIdentical


# NOTE: When running test, a window will show up, just close the window.
# Default configs:
#   Compactness: 1
#   Marker: 10

def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    ground_truth_objs_path = config.pop('groundTruthObjectPath')
    ground_truth_mask_path = config.pop('groundTruthMaskPath')
    SuperpixelPainter.run(params=config)
    assert isIdentical(ground_truth_objs_path, config.get("resultObjectPath"))
    
    assert isIdentical(ground_truth_mask_path, config.get("resultMaskPath"))
    return True

class Test_SuperpixelPainter(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "Inputs","SuperpixelPainter_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_SuperpixelPainter_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_SuperpixelPainter, test_name, test_method)


if __name__ == "__main__":
    unittest.main()