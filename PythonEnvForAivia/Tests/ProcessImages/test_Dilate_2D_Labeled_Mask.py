import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import Dilate_2D_Labeled_Mask
from Tests.utils.comparison import isIdentical


'''
Dilate 2D labeled masks.'''


def run_test(config):
    config['unitTest'] = True
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = Dilate_2D_Labeled_Mask.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_Dilate_2D_Labeled_Mask(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

print("* [TEST] ProcessImages > Dilate_2D_Labeled_Mask")

config_json_path = os.path.join(os.path.dirname(__file__), "Dilate_2D_Labeled_Mask", "Config_Dilate_2D_Labeled_Mask.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_Dilate_2D_Labeled_Mask_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_Dilate_2D_Labeled_Mask, test_name, test_method)


if __name__ == "__main__":
    unittest.main()