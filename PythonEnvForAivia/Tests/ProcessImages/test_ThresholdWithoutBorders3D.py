import unittest
import json
import os
from Recipes.ProcessImages import ThresholdWithoutBorders3D
from Tests.utils.comparison import isIdentical


'''
Thresholds an image for segmentation, then clears any objects intersecting the image borders before
creating an object set in Aivia.

This recipe only works in 3D. Use ThresholdWithoutBorders2D instead for 2D cases.

Aivia's mesh creation engine will not automatically label meshes it creates in 3D, so we must
explicitly label the objects we pass to Aivia. Aivia will also not accept images returned as
a different bit depth than their input. Therefore, the user is recommended to convert their
input channel to 16bit (right-click the channel > convert to > 16 bit) in Aivia before
applying this recipe if they expect more than 255 objects to be segmented.'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = ThresholdWithoutBorders3D.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('resultObjectPath'))

    return True

class Test_ThresholdWithoutBorders3D(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ThresholdWithoutBorders3D", "Config_ThresholdWithoutBorders3D.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ThresholdWithoutBorders3D_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ThresholdWithoutBorders3D, test_name, test_method)


if __name__ == "__main__":
    unittest.main()