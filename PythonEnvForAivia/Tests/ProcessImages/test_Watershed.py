import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import Watershed
from Tests.utils.comparison import isIdentical


'''
Simple watershed.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = Watershed.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_Watershed(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "Watershed", "Config_Watershed.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_Watershed_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_Watershed, test_name, test_method)


if __name__ == "__main__":
    unittest.main()