import unittest
from main import get_greeting


class TestMain(unittest.TestCase):
    def test_default_greeting(self):
        self.assertEqual(get_greeting(), "Hello, World!")

    def test_custom_greeting(self):
        self.assertEqual(get_greeting("Ultron"), "Hello, Ultron!")


if __name__ == "__main__":
    unittest.main()
