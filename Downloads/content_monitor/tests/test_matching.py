import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.matching import compute_score


class TestComputeScore(unittest.TestCase):

    def test_exact_match_title(self):
        self.assertEqual(compute_score("django", "Learn Django Today", "Nothing here"), 100)

    def test_exact_match_case_insensitive(self):
        self.assertEqual(compute_score("PYTHON", "python tutorials", "body"), 100)

    def test_partial_match_title(self):
        self.assertEqual(compute_score("python", "All about pythons", "body"), 70)

    def test_body_only_match(self):
        self.assertEqual(compute_score("django", "Cooking tips", "Django is great"), 40)

    def test_no_match(self):
        self.assertEqual(compute_score("django", "Cooking tips", "Best recipes ever"), 0)

    def test_title_beats_body(self):
        self.assertEqual(compute_score("python", "Python is great", "Also python is fun"), 100)

    def test_multi_word_phrase_exact(self):
        self.assertEqual(compute_score("data pipeline", "Building a Data Pipeline", "body"), 100)

    def test_multi_word_phrase_body_only(self):
        self.assertEqual(compute_score("machine learning", "AI Basics", "This covers machine learning"), 40)


if __name__ == "__main__":
    unittest.main()