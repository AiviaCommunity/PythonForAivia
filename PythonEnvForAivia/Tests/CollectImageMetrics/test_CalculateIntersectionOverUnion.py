import unittest
import json
import os
import ctypes
from Recipes.CollectImageMetrics import CalculateIntersectionOverUnion
from Tests.utils.comparison import isIdentical


'''
Calculates Intersection over Union value considering intensity above or equal 1 as a positive mask
Side note: IoU values are output in the log (File > Options > Logging > Open)

Returns
-------
New channel to show intersection mask.
Pressing CTRL+C after the popup window appears allow you to copy the text in the window.
To be able to see the printed info in the log file, set:
File > Options > Logging > Verbosity = everything'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    ground_truth_value_2 = config.pop('groundTruthValue_2')

    result_value = CalculateIntersectionOverUnion.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))
    assert (str(result_value) == str(ground_truth_value_2)), f'Expected {ground_truth_value_2} but result was {result_value}'

    return True

class Test_CalculateIntersectionOverUnion(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "CalculateIntersectionOverUnion", "Config_CalculateIntersectionOverUnion.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_CalculateIntersectionOverUnion_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_CalculateIntersectionOverUnion, test_name, test_method)


if __name__ == "__main__":
    unittest.main()