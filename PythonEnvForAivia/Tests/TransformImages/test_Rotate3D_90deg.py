import unittest
import json
import os
from Recipes.TransformImages import Rotate3D_90deg
from Tests.utils.comparison import isIdentical


'''
Scales the input channel up or down (isotropic factor) and rotates the volume 90 degrees around one axis (not centered).
Works only for 3D (not timelapses) and for single channels.
Output path is given with "params" for test and hardcoded for regular run in Aivia
NOTE: when Magicgui panel appears, select Y - Clockwise'''


def run_test(config):
	ground_truth_path_2 = config.pop('groundTruthPath_2')
	file_output_value_2 = config.get('fileOutputPath_2')
	test_guidance = config.pop('testGuidance')
	ctypes.windll.user32.MessageBoxW(0, test_guidance, 'Test guidance', 0)

    result_value = Rotate3D_90deg.run(params=config)
    
	assert isIdentical(ground_truth_path_2, file_output_value_2)

    return True

class Test_Rotate3D_90deg(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "Rotate3D_90deg", "Config_Rotate3D_90deg.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_Rotate3D_90deg_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_Rotate3D_90deg, test_name, test_method)


if __name__ == "__main__":
    unittest.main()