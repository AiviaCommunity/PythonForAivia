import unittest
import json
import os
import ctypes
from Recipes.TransformImages import StackReg_2DImageAlignment_2channels
from Tests.utils.comparison import isIdentical


'''
Performs a 2D registration for timelapses, using PyStackReg. 
Only one channel is used for auto-alignment detection, the other one is processed the same way as the first one.
Methods:
- Previous = Use previous image to calculate registration
- First = First timepoint is used as the fixed reference.'''


def run_test(config):
    config['unitTest'] = True
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    ground_truth_path_2 = config.pop('groundTruthPath_2')

    result_value = StackReg_2DImageAlignment_2channels.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath2'))
    assert isIdentical(ground_truth_path_2, config.get('resultPath1'))

    return True

class Test_StackReg_2DImageAlignment_2channels(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

print("* [TEST] TransformImages > StackReg_2DImageAlignment_2channels")

config_json_path = os.path.join(os.path.dirname(__file__), "StackReg_2DImageAlignment_2channels", "Config_StackReg_2DImageAlignment_2channels.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_StackReg_2DImageAlignment_2channels_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_StackReg_2DImageAlignment_2channels, test_name, test_method)


if __name__ == "__main__":
    unittest.main()