import unittest
import numpy as np
import test as ts

class RaceTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_frog(self):
        fg = ts.Frogs().frog()
        a = np.array([1., 2.])
        np.testing.assert_array_equal(a, fg)
        # self.assertEqual(np.array([1., 2.]), fg)

if __name__ == "__main__":

    unittest.main(exit=False)