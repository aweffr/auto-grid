from .utils import *


class Project(object):
    # json_path = "E:/AbaqusDir/auto/output"
    # abaqus_dir = "E:/AbaqusDir/sym-40/abaqus-files"
    abaqus_exe_path = "C:/SIMULIA/Abaqus/6.14-2/code/bin/abq6142.exe"
    script_path = "E:/AbaqusDir/auto/abaqus_api"
    pre_script_name = "pre.py"
    post_script_name = "post.py"

    def __init__(self, project_name, json_path, abaqus_dir, iter_times=10, step_factor=0.25, enable_rand=False):
        self.project_name = project_name
        self.json_path = json_path
        self.abaqus_dir = abaqus_dir
        self.enable_rand = enable_rand
        self.abaqus_env = RunAbaqus(
            abaqus_exe_path=self.abaqus_exe_path,
            abaqus_dir=abaqus_dir,
            script_path=self.script_path,
            pre_script=self.pre_script_name,
            post_script=self.post_script_name
        )
        self.iter_times = iter_times
        self.step_factor = step_factor

    def run(self, pt_list):
        for time in range(self.iter_times):
            print("time:%d" % time, "pt_list=\n", pt_list)
            plain = InitPlain(pt_list)
            # plain.plot_xy()
            plain.save_fig("%s-%d" % (self.project_name, time), self.json_path)
            res_file_prefix = "res_"
            tmp_1st_name = "%s-1st-%d.json" % (self.project_name, time)
            tmp_2nd_name = "%s-2nd-%d.json" % (self.project_name, time)
            d_1st = plain.to_json(file_name=tmp_1st_name, save_path=self.json_path)

            abq_name = "%s-%d" % (self.project_name, time)
            d_2nd = GenerateAbaqusData.to_json(
                d_in=d_1st,
                json_file_name=tmp_2nd_name,
                res_file_prefix=res_file_prefix,
                json_save_dir=self.json_path,
                abaqus_dir=self.abaqus_dir,
                mdb_name=abq_name,
                odb_name=abq_name,
                iter_time=time,
                left_hang=10,
                left_hang_height=5,
                right_hang=30,
                right_hang_height=5,
                radius=0.02,
                thickness=0.003,
                elastic_modular=26E+09,
                density=1850,
                deformation_step_name="Step-1",
            )

            self.abaqus_env.pre_process(self.json_path, tmp_2nd_name)
            self.abaqus_env.post_process(self.json_path, tmp_2nd_name)

            res_file_name = res_file_prefix + abq_name + ".json"
            with open(self.json_path + "/" + res_file_name, "r") as f:
                d = json.load(f)
                print("bound_stderr=", d['bound_stderr'])

            # factor = self.step_factor * random() + 0.05
            factor = self.step_factor

            iter = Iteration(d, factor=factor, enable_rand=self.enable_rand)
            pt_list = iter.get_new_points()


if __name__ == '__main__':
    pass
