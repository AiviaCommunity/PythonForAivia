import unittest
import json
import os
import ctypes
from Recipes.TransformImages import MaxIntensityProjection
from Tests.utils.comparison import isIdentical


'''
Performs a maximum intensity projection through Z for a single channel.
Works only in 3D (not 3D+t yet).'''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    ground_truth_path_2 = config.pop('groundTruthPath_2')
    file_output_value_2 = config.get('fileOutputPath_2')

    result_value = MaxIntensityProjection.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))
    assert isIdentical(ground_truth_path_2, file_output_value_2)

    return True

class Test_MaxIntensityProjection(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "MaxIntensityProjection", "Config_MaxIntensityProjection.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_MaxIntensityProjection_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_MaxIntensityProjection, test_name, test_method)


if __name__ == "__main__":
    unittest.main()