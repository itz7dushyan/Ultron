"""
Unit tests for TestProject main module.
"""
import unittest
from main import get_hello_message

class TestMain(unittest.TestCase):
    def test_get_hello_message_default(self):
        self.assertEqual(get_hello_message(), "Hello, World!")

    def test_get_hello_message_custom(self):
        self.assertEqual(get_hello_message("Ultron"), "Hello, Ultron!")

if __name__ == "__main__":
    unittest.main()
