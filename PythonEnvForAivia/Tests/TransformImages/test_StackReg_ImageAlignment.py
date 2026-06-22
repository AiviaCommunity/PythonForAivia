import unittest
import json
import os
import ctypes
from Recipes.TransformImages import StackReg_ImageAlignment
from Tests.utils.comparison import isIdentical


'''
Performs a 2D registration for timelapses, using PyStackReg. No parameters available (default ones only).
Methods:
- Previous = Use previous image to calculate registration
- First = First timepoint is used as the fixed reference.
NOTE: Use default GUI options'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    test_guidance = config.pop('testGuidance')
    ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)

    result_value = StackReg_ImageAlignment.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_StackReg_ImageAlignment(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "StackReg_ImageAlignment", "Config_StackReg_ImageAlignment.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_StackReg_ImageAlignment_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_StackReg_ImageAlignment, test_name, test_method)


if __name__ == "__main__":
    unittest.main()