import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import ReplicateFirstTimeFrame
from Tests.utils.comparison import isIdentical


'''
Replicates the first image in a time series to all other time frames.
Useful when a fixed mask needs to be replicated over time.'''


def run_test(config):
    config['unitTest'] = True
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = ReplicateFirstTimeFrame.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('outputImagePath'))

    return True

class Test_ReplicateFirstTimeFrame(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

print("* [TEST] ProcessImages > ReplicateFirstTimeFrame")

config_json_path = os.path.join(os.path.dirname(__file__), "ReplicateFirstTimeFrame", "Config_ReplicateFirstTimeFrame.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ReplicateFirstTimeFrame_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ReplicateFirstTimeFrame, test_name, test_method)


if __name__ == "__main__":
    unittest.main()