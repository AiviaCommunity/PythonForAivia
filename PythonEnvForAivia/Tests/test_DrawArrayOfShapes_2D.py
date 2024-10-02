import unittest
import json
import os
from Recipes.ProcessImages import DrawArrayOfShapes_2D
from Tests.utils.comparison import isIdentical

# NOTE: When running test, a GUI will pop up for each test.  
# Press `Reset values to default (96 multiwell template)` and then
# set `Number of shapes in the same row` to `2` and
# set `Number of shapes in the same column` to `2`.
# This is to prevent the array drawer from drawing outside of the image 
# and causing an error

def run_test(config):
    # Dummy test logic for now
    ground_truth_path = config.pop('groundTruthPath')
    DrawArrayOfShapes_2D.run(params=config)
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    return True

class Test_DrawArrayOfShapes_2D(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "Inputs","DrawArrayOfShapes_2D_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AdjustGamma_MagicGui_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_DrawArrayOfShapes_2D, test_name, test_method)


if __name__ == "__main__":
    unittest.main()