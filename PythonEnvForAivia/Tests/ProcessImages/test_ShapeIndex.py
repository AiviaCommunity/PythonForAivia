import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import ShapeIndex
from Tests.utils.comparison import isIdentical


'''
Computes the shape index as derived from the eigenvalues of the Hessian
and returns it as a new channel scaled to 8bit space.

Different values indicate convexity/concavitiy and shapes:
 - cups / caps
 - troughs / domes
 - ruts / ridges
 - saddle ruts / saddle ridges
 - saddles'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = ShapeIndex.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_ShapeIndex(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ShapeIndex", "Config_ShapeIndex.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ShapeIndex_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ShapeIndex, test_name, test_method)


if __name__ == "__main__":
    unittest.main()