import unittest
import json
import os
from Recipes.ProcessImages import SuperpixelPainter
from Tests.utils.comparison import isIdentical


'''
Compute watershed superpixels on an Aivia channel and create a mask from that painting.
Usability note! This plugin currently only works under certain conditions:
- Image is 2D only (no time)
- Image is smaller than the size of the screen

Improvements that would make this more usable are:
- Add ability to change color of painted mask
- Add ability to change color of superpixel boundaries
- Convert the Compactness slider to a log scale
- Scale image to screen size (need convert selected pixels by scaling factor)
NOTE: When running test, a GUI will pop up for each test. Default configs: Compactness: 1, Marker: 10'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')
	ground_truth_path_2 = config.pop('groundTruthPath_2')
	test_guidance = config.pop('testGuidance')
	ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)

    result_value = SuperpixelPainter.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('resultObjectPath'))
	assert isIdentical(ground_truth_path_2, config.get('resultMaskPath'))

    return True

class Test_SuperpixelPainter(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "SuperpixelPainter", "Config_SuperpixelPainter.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_SuperpixelPainter_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_SuperpixelPainter, test_name, test_method)


if __name__ == "__main__":
    unittest.main()