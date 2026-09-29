import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import SubtractBackground_RollingBall
from Tests.utils.comparison import isIdentical


'''
Process a single channel image to subtract the background.
See: https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.rolling_ball'''


def run_test(config):
    config['unitTest'] = True
    ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = SubtractBackground_RollingBall.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultImagePath'))

    return True

class Test_SubtractBackground_RollingBall(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

print("* [TEST] ProcessImages > SubtractBackground_RollingBall")

config_json_path = os.path.join(os.path.dirname(__file__), "SubtractBackground_RollingBall", "Config_SubtractBackground_RollingBall.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_SubtractBackground_RollingBall_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_SubtractBackground_RollingBall, test_name, test_method)


if __name__ == "__main__":
    unittest.main()