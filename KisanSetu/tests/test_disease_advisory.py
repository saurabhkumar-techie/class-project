import unittest

from disease_advisory import get_advisory


class DiseaseAdvisoryTests(unittest.TestCase):
    def test_returns_crop_and_symptom_guidance(self):
        result = get_advisory("tomato", "leaf_spots")

        self.assertIn("Early or late blight", result["possible_cause"])
        self.assertIn("not a diagnosis", result["possible_cause"])
        self.assertTrue(result["steps"])
        self.assertIn("registered", result["pesticide"])

    def test_does_not_recommend_pesticide_for_yellowing_alone(self):
        result = get_advisory("rice", "yellowing")

        self.assertIn("No pesticide", result["pesticide"])

    def test_rejects_unknown_crop_or_symptom(self):
        self.assertIsNone(get_advisory("unknown", "leaf_spots"))
        self.assertIsNone(get_advisory("rice", "unknown"))


if __name__ == "__main__":
    unittest.main()
