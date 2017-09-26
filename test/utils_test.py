from __future__ import print_function
import unittest
from src.utils.utils import *
from src.utils.run_abaqus import *


class UtilsTest(unittest.TestCase):
    def setUp(self):
        super(UtilsTest, self).setUp()
        abaqus_dir = "E:/AbaqusDir/sym-40/abaqus-files"
        abaqus_exe_path = "C:/SIMULIA/Abaqus/6.14-2/code/bin/abq6142.exe"

        script_path = "E:/AbaqusDir/auto/abaqus_api"
        pre_script_name = "pre.py"
        post_script_name = "post.py"

        self.abaqus_env = RunAbaqus(
            abaqus_exe_path=abaqus_exe_path,
            abaqus_dir=abaqus_dir,
            script_path=script_path,
            pre_script=pre_script_name,
            post_script=post_script_name
        )

    def test_a_GenerateCurve(self):
        # test unit
        test = [(0, 0), (2, 6.2), (10, 13), (20, 11.5), (30, 13), (38, 6.2), (40, 0)]
        tc = InitPlain(test)
        tc.to_json(file_name="test_output.json")
        # tc.plot_xy()

    def test_b_Generate3DPoint(self):
        with open("test_output.json", "r") as f:
            d = json.load(f)
        xcoord = d['xcoord']
        incoord = d['incoord']
        print(GenerateAbaqusData.to_3d(xcoord))
        print(GenerateAbaqusData.to_3d(incoord))

    def test_c_GenerateOutput(self):
        with open("test_output.json", "r") as f:
            d = json.load(f)
        GenerateAbaqusData.to_json(
            d_in=d,
            json_file_name="pre_post_finish.json",
            json_save_dir="E:/AbaqusDir/auto/output",
            abaqus_dir="E:/AbaqusDir/sym-40/abaqus-files",
            mdb_name="pm1508",
            odb_name="pm1508",
            iter_time=0,
            left_hang=10,
            left_hang_height=5,
            right_hang=30,
            right_hang_height=5,
            radius=0.02,
            thickness=0.003,
            elastic_modular=26E+09,
            density=1850,
            deformation_step_name="Step-1"
        )

    def test_d_RunAbaqusPre(self):
        json_path = "E:/AbaqusDir/auto/output"
        json_file_name = "pre_post_finish.json"
        self.abaqus_env.pre_process(json_path, json_file_name)

    def test_e_RunAbaqusPost(self):
        json_path = "E:/AbaqusDir/auto/output"
        json_file_name = "pre_post_finish.json"
        self.abaqus_env.post_process(json_path, json_file_name)

    def tearDown(self):
        super(UtilsTest, self).tearDown()


if __name__ == '__main__':
    unittest.main()
