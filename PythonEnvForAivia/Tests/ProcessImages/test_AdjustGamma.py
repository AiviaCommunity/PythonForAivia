import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import AdjustGamma
from Tests.utils.comparison import isIdentical


'''
Adjusts gamma of the input channel pixelwise according to O = I**gamma.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = AdjustGamma.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_AdjustGamma(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "AdjustGamma", "Config_AdjustGamma.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AdjustGamma_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_AdjustGamma, test_name, test_method)


if __name__ == "__main__":
    unittest.main()