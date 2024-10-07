import unittest
import json
import os
from Recipes.ConvertImagesForAivia import AiviaExperimentCreator
from Tests.utils.comparison import isJsonIdentical


import os
import glob


# FOR TESTING YOU MUST MANUALLY SELECT THESE TWO FILES WHEN THE PROMPT COMES UP
# Select the following image and hit OK
# PythonEnvForAivia\Tests\InputTestImages\Test_8bit_YX_BinaryCylinder1_MaxIP.tif
# When the prompt asks you if you want to select more images, select the following image and hit OK
# PythonEnvForAivia\Tests\InputTestImages\Test_8bit_YX_BinaryCylinder2_MaxIP.tif
# When the prompt asks you if you want to select more images, hit NO and proceed with continuing the recipe.

def find_experiment_file(directory):
    files = glob.glob(os.path.join(directory, "*.aiviaexperiment"))
    return files[0] if files else None

def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    ground_truth_filepath = find_experiment_file(ground_truth_path)
    result_filepath = find_experiment_file(config.get("resultPath"))
    print(ground_truth_filepath)
    print(result_filepath)
    AiviaExperimentCreator.run(config)

    assert isJsonIdentical(ground_truth_filepath, result_filepath)
    return True

class Test_AiviaExperimentCreator(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","AiviaExperimentCreator_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_AiviaExperimentCreator_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_AiviaExperimentCreator, test_name, test_method)


if __name__ == "__main__":
    unittest.main()