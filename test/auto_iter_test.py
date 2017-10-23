import unittest

from src.auto_iter import *


class AutoIterTest(unittest.TestCase):
    def setUp(self):
        super().setUp()

    def test_a_iter10times(self):
        proj = Project(project_name="luck-with-rand",
                       json_path="E:/AbaqusDir/auto/output",
                       abaqus_dir="E:/AbaqusDir/sym-40/abaqus-files",
                       step_factor=0.33, enable_rand=True,
                       iter_times=250)

        pt_list = [(0, 0), (2, 6.2), (10, 13), (20, 11.5), (30, 13), (38, 6.2), (40, 0)]

        proj.run(pt_list)

    def tearDown(self):
        super().tearDown()


if __name__ == '__main__':
    unittest.main()
