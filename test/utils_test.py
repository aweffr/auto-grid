import unittest
from src.utils.utils import *


class UtilsTest(unittest.TestCase):
    def setUp(self):
        super(UtilsTest, self).setUp()

    def testGenerateCurve(self):
        # test unit
        test = [(0, 0), (2, 6.2), (10, 13), (20, 11.5), (30, 13), (38, 6.2), (40, 0)]
        tc = InitPlain(test)
        tc.to_json(file_name="test_output.json")
        tc.plot_xy()

    def tearDown(self):
        super(UtilsTest, self).tearDown()


if __name__ == '__main__':
    unittest.main()
