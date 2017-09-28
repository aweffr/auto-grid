import unittest

from src.utils.iter import *


class IterTest(unittest.TestCase):
    def setUp(self):
        super(IterTest, self).setUp()

    def test_a_avg_space_point(self):
        p_b = (0, 1, 0, 1, 2, 2)
        p_in = (0, 2, 0, 1, 2.5, 1.2)
        relation = Iteration.relation(p_b, p_in)
        self.assertEqual(relation, 'y')

        avg_val = 1.0

        pt = Iteration.avg_space_point(p_b, p_in, avg_val)
        print(pt)

    def test_b_generate_new_plain(self):
        odb_file_name = "res_auto777-3.json"
        odb_file_path = "E:/AbaqusDir/auto/output"
        with open(odb_file_path + "/" + odb_file_name, "r") as f:
            d = json.load(f)
        iter = Iteration(d, factor=0.4)
        iter.plot_raw_result()
        new_plain = iter.generate_new_plain()
        new_plain.to_json("iter6.json", save_path=odb_file_path)
        new_plain.plot_xy()

    def tearDown(self):
        super(IterTest, self).tearDown()


if __name__ == '__main__':
    unittest.main()
