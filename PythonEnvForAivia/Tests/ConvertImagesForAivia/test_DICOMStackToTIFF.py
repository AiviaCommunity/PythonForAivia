import unittest
import json
import os
from Recipes.ConvertImagesForAivia import DICOMStackToTIFF
from Tests.utils.comparison import isIdentical


def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    DICOMStackToTIFF.dicom_to_tiff(config.get('dicom_directory'), 
                                   bit_depth='16', 
                                   output_path=config.get('resultPath'))
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    return True

class Test_DICOMStackToTIFF(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","DICOMStackToTIFF_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_DICOMStackToTIFF_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_DICOMStackToTIFF, test_name, test_method)


if __name__ == "__main__":
    unittest.main()