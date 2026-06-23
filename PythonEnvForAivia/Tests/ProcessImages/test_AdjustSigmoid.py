import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import AdjustSigmoid
from Tests.utils.comparison import isIdentical


'''
Performs a Sigmoid contrast adjustment. Think of the "cutoff" being a number 0 - 1,
representing a percentile of the histogram, above and below which the histogram is
"squished" to its bounds. The gain controls the amount of "squishing".

In mathematical terms, O = 1 / (1 + exp*(gain*(cutoff - I))).

Note that this transform is prone to returning a wildly different dynamic range than
the input image and should be parameterized carefully.'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = AdjustSigmoid.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_AdjustSigmoid(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "AdjustSigmoid", "Config_AdjustSigmoid.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AdjustSigmoid_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_AdjustSigmoid, test_name, test_method)


if __name__ == "__main__":
    unittest.main()