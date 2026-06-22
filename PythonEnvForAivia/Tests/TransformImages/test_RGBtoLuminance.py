import unittest
import json
import os
from Recipes.TransformImages import RGBtoLuminance
from Tests.utils.comparison import isIdentical


'''
Computes the luminance of an RGB image and returns that as a new channel.

Useful when images are saved as RGB (e.g. histopathology, photographs, etc.)
and the user desires to apply a recipe or pixel classifier to only one
channel, but wishes to retain the maximum amount of information from each.

The luminance has a 30% contribution from the red channel, 59%
contribution from the green channel, and 11% contribution from the
blue channel.

NOTE: Default is not to show the histogram (=0). The option can be turned on once when running the test manually, but no GT is expected'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')
	test_guidance = config.pop('testGuidance')
	ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)

    result_value = RGBtoLuminance.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('gray_c'))

    return True

class Test_RGBtoLuminance(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "RGBtoLuminance", "Config_RGBtoLuminance.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_RGBtoLuminance_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_RGBtoLuminance, test_name, test_method)


if __name__ == "__main__":
    unittest.main()