import unittest
import json
import os
import ctypes
from Recipes.ProcessImages import AdjustGamma_MagicGui
from Tests.utils.comparison import isIdentical


'''
Adjusts gamma of the input channel pixelwise according to O = I**gamma.
This extra version of this script is a good example on how to quickly implement a GUI popup with MagicGui.
NOTE: When running test, a GUI will pop up for each test. Select 0.75 and press Run '''


def run_test(config):
    ground_truth_path_1 = config.pop('groundTruthPath_1')
    test_guidance = config.pop('testGuidance')
    ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)

    result_value = AdjustGamma_MagicGui.run(params=config)
    
    assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_AdjustGamma_MagicGui(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "AdjustGamma_MagicGui", "Config_AdjustGamma_MagicGui.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AdjustGamma_MagicGui_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_AdjustGamma_MagicGui, test_name, test_method)


if __name__ == "__main__":
    unittest.main()