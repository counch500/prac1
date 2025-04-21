import unittest
from func import sqroots

class TestSqroots(unittest.TestCase):
    def test_two_roots(self):
        self.assertEqual(sqroots("1 -3 2"), "2.0 1.0")
    
    def test_one_root(self):
        self.assertEqual(sqroots("1 2 1"), "-1.0")
    
    def test_no_roots(self):
        self.assertEqual(sqroots("1 1 1"), "")
    
    def test_exceptions(self):
        with self.assertRaises(ValueError):
            sqroots("1 2")
        
        with self.assertRaises(ValueError):
            sqroots("0 2 3")
       
        with self.assertRaises(ValueError):
            sqroots("a b c")
if __name__ == '__main__':
    unittest.main()
