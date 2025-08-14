import unittest
import json
import os
from Recipes.ProcessImages import MaxSlices
from Tests.utils.comparison import isIdentical


def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    MaxSlices.run(params=config)
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    return True

class Test_MaxSlices(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","MaxSlices_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_MaxSlices_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_MaxSlices, test_name, test_method)


if __name__ == "__main__":
    unittest.main()