import unittest
import json
import os
from Recipes.CollectImageMetrics import CalculateIntersectionOverUnion
from Tests.utils.comparison import isIdentical


def run_test(config):
    ground_truth_path = config.pop('groundTruthPath')
    ground_truth_value = config.pop('groundTruthValue')
    result_value = CalculateIntersectionOverUnion.run(config)
    assert isIdentical(ground_truth_path, config.get("resultPath"))
    assert (result_value == ground_truth_value), f'Expected {groundTruthValue} but result was {result_value}'
    return True

class Test_CalculateIntersectionOverUnion(unittest.TestCase):
    def dynamic_test_generator(self, config):
        self.assertTrue(run_test(config))

def generate_test_method(config):
    def test_method(self):
        self.dynamic_test_generator(config)
    return test_method

config_json_path = os.path.join(os.path.dirname(__file__), "TestConfigs","CalculateIntersectionOverUnion_configs.json")
with open(config_json_path) as f:
    configurations = json.load(f)

# Dynamically create test methods for each configuration
for i, config in enumerate(configurations):
    test_name = f"test_CalculateIntersectionOverUnion_{i:02d}"  # Must start with "test_"
    test_method = generate_test_method(config)
    setattr(Test_CalculateIntersectionOverUnion, test_name, test_method)


if __name__ == "__main__":
    unittest.main()