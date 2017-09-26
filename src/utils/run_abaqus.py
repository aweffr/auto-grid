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
"""


class RunAbaqus(object):
    """
    直接Popen中打abaqus 开头的命令会得到文件无效的Windows Error返回值。
    要找到exe的路径.
    """

    def __init__(self, abaqus_dir, abaqus_bin_dir):
        self.abaqus_exe = self.__get_abaqus_exe(abaqus_bin_dir)
        self.abaqus_dir = abaqus_dir

    def pre_pocess(self, script_path, script_name, json_path, json_file_name):
        script = script_path + "/" + script_name
        args = ["C:/SIMULIA/Abaqus/6.14-2/code/bin/abq6142.exe", "cae", "noGUI=%s" % script]
        env = os.environ.copy()
        env["JSON"] = json_path + "/" + json_file_name
        print("args=", args, "env=", env)
        try:
            p = subprocess.Popen(args, cwd=self.abaqus_dir, stdout=PIPE, env=env)
            res = p.communicate()
            for line in res:
                line = line.decode("gbk")
                print(line)
        except Exception as e:
            print(e)

    def __get_abaqus_exe(self, abaqus_bin_dir):
        pass
