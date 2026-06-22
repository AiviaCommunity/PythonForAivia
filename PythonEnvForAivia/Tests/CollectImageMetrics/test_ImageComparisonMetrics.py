import unittest
import json
import os
from Recipes.CollectImageMetrics import ImageComparisonMetrics
from Tests.utils.comparison import isIdentical


'''
Calculates SSIM map as a result of the comparison of 2 channels and metrics values (in the log file). 

For the output image, it is highly recommended to use LUT color mapping to better see the variations in the SSIM values
All real SSIM values (ranging from 0 to 1) can be retrieved from the map doing the following: divide intensities by 255 if image is 8-bit, or by 65535 if 16-bit.

Side note: MSE and mean SSIM (and NRMSE, PSNR) values are output in the log
To be able to see the printed info in the log file, set:
File > Options > Logging > Verbosity = Everything

Parameters
----------
First input: image to compare (e.g.Deep Learning restored image)
Second input: reference (e.g. Ground Truth image), the one adjusted by histogram matching.
IMPORTANT: Input channels need to have the same bit depth'''


def run_test(config):
	ground_truth_path_1 = config.pop('groundTruthPath_1')
	ground_truth_path_2 = config.pop('groundTruthPath_2')
	ground_truth_value_list_3 = config.pop('groundTruthValueList_3')

    result_value = ImageComparisonMetrics.run(params=config)
    
	assert isIdentical(ground_truth_path_1, config.get('resultPath'))
	assert isIdentical(ground_truth_path_2, config.get('resultPathAdj'))
	n_values = len(result_value)   # Expected to contain multiple values
	for val_ind in range(n_values):
		assert (result_value[val_ind] == ground_truth_value_list_3[val_ind]), f'Expected {ground_truth_value_list_3[val_ind]} but result was {result_value[val_ind]}'

    return True

class Test_ImageComparisonMetrics(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "ImageComparisonMetrics", "Config_ImageComparisonMetrics.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_ImageComparisonMetrics_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_ImageComparisonMetrics, test_name, test_method)


if __name__ == "__main__":
    unittest.main()