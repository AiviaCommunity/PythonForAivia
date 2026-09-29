import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import Arithmetics_SingleChannel
from Tests.utils.comparison import isIdentical


'''
Various arithmetics to be applied to one channel (0=multiply, 1=divide, 2=add, 3=subtract).'''


def run_test(config):
    config['unitTest'] = True
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = Arithmetics_SingleChannel.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultImagePath'))

    return True

class Test_Arithmetics_SingleChannel(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

print("* [TEST] ProcessImages > Arithmetics_SingleChannel")

config_json_path = os.path.join(os.path.dirname(__file__), "Arithmetics_SingleChannel", "Config_Arithmetics_SingleChannel.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_Arithmetics_SingleChannel_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_Arithmetics_SingleChannel, test_name, test_method)


if __name__ == "__main__":
    unittest.main()