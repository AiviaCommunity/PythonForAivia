import unittest
import json
import os
from Recipes.ProcessImages import AdjustGamma_MagicGui
from Tests.utils.comparison import isIdentical

# NOTE: When running test, a GUI will pop up for each test.  
# The interface will ask for a value for gamma. Set it to `0.75`
# or resultant images will not match ground truth files stored.

def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    AdjustGamma_MagicGui.run(params=config)
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    return True

class Test_AdjustGamma_MagicGui(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "Inputs","AdjustGamma_MagicGui_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AdjustGamma_MagicGui_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_AdjustGamma_MagicGui, test_name, test_method)


if __name__ == "__main__":
    unittest.main()