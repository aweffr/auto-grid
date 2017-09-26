# coding=utf-8
from __future__ import print_function
import subprocess
from subprocess import PIPE
import os
import glob

# TODO: 自动locate abaqus前处理器的路径
# TODO: 搞明白abaqus目前重定向到abq.exe的机制
"""
直接Popen中打abaqus 开头的命令会得到文件无效的命令。要找到exe的路径
"C:/SIMULIA/Abaqus/6.14-2/code/bin/abq6142.exe"
"""


class RunAbaqus(object):
    """
    直接Popen中打abaqus 开头的命令会得到文件无效的Windows Error返回值。
    要找到exe的路径.
    """

    def __init__(self, abaqus_dir, abaqus_exe_path, script_path, pre_script, post_script):
        self.abaqus_exe_path = abaqus_exe_path
        self.abaqus_dir = abaqus_dir
        self.script_path = script_path
        self.pre_script = pre_script
        self.post_script = post_script

    @classmethod
    def exec_script(cls, abaqus_exe_path, script_path, script_name, json_path, json_file_name, abaqus_dir=os.getcwd()):
        script = script_path + "/" + script_name
        args = [abaqus_exe_path, "cae", "noGUI=%s" % script]
        env = os.environ.copy()
        env["JSON"] = json_path + "/" + json_file_name
        try:
            p = subprocess.Popen(args, cwd=abaqus_dir, stdout=PIPE, env=env)
            res = p.communicate()
            for line in res:
                if line is not None:
                    line = line.decode("gbk")
                    print(line)
        except Exception as e:
            print(e)
            return False
        return True

    def pre_process(self, json_path, json_file_name):
        ret = self.exec_script(
            abaqus_exe_path=self.abaqus_exe_path,
            script_path=self.script_path,
            script_name=self.pre_script,
            json_path=json_path,
            json_file_name=json_file_name,
            abaqus_dir=self.abaqus_dir
        )
        script = self.script_path + "/" + self.pre_script
        if ret:
            print("%s success!" % script)
        else:
            print("%s fail!" % script)

    def post_process(self, json_path, json_file_name):
        ret = self.exec_script(
            abaqus_exe_path=self.abaqus_exe_path,
            script_path=self.script_path,
            script_name=self.post_script,
            json_path=json_path,
            json_file_name=json_file_name,
            abaqus_dir=self.abaqus_dir
        )
        script = self.script_path + "/" + self.post_script
        if ret:
            print("%s success!" % script)
        else:
            print("%s fail!" % script)
