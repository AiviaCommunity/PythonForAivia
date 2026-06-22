import unittest
import json
import os
from Recipes.ProcessImages import MeijeringNeuriteness
from Tests.utils.comparison import isIdentical


'''
Finds and enhances bright ridges within the image that are within a reasonable
range of the size given by the user. Returns a max projection through scale space
for 5 evenly-spaced Gaussian sigmas.

Because np.arange() is used to contruct the array of sigma values, the largest
sigma is excluded.
https://docs.scipy.org/doc/numpy/reference/generated/numpy.arange.html

For example, if the user specifies min and max sigmas of 0.1 and 0.6, respectively,
the transform is performed for Gaussian sigma values of 0.1, 0.2, 0.3, 0.4, 0.5.
The maximum values from all of the transforms is output at every voxel.'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')

    result_value = MeijeringNeuriteness.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('resultPath'))

    return True

class Test_MeijeringNeuriteness(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "MeijeringNeuriteness", "Config_MeijeringNeuriteness.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_MeijeringNeuriteness_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_MeijeringNeuriteness, test_name, test_method)


if __name__ == "__main__":
    unittest.main()