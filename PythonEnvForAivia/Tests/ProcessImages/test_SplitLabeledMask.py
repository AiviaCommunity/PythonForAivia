import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import SplitLabeledMask
from Tests.utils.comparison import isIdentical


'''
Separates labeled objects in a mask (2D or 3D).
For instance, CellPose and StarDist output masks where objects can touch each other.
In Aivia, objects need to be separated to be measurable.

Works only when there is no time dimension (yet).'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = SplitLabeledMask.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_SplitLabeledMask(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "SplitLabeledMask", "Config_SplitLabeledMask.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_SplitLabeledMask_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_SplitLabeledMask, test_name, test_method)


if __name__ == "__main__":
    unittest.main()