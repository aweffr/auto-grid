# -*- coding:utf-8 -*-

import json
import os
from itertools import chain
from math import floor, ceil
from operator import itemgetter

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.optimize import brenth

from .my_types import Point2

DEBUG = True


class Common(object):
    @staticmethod
    def distance(p1, p2):
        dis = abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        return dis

    @staticmethod
    def xlist(inlst):
        # inlst format:[(a1,b1), (a2,b2),....(an,bn)]
        # out format: [a1, a2, a3, ..., an]
        return [x[0] for x in inlst]

    @staticmethod
    def ylist(inlst):
        # inlst format same as xlist
        # out format: [b1, b2, b3, ..., bn]
        return [x[1] for x in inlst]

    @staticmethod
    def zlist(inlst):
        return [x[2] for x in inlst]

    @staticmethod
    def get_spl(pt_list):
        """根据点坐标的列表生成spline。
        :param pt_list: [(a1,b1), (a2,b2),....(an,bn)]
        :return: InterpolatedUnivariateSpline
        """
        pt_list = sorted(pt_list, key=itemgetter(0))
        xx, yy = Common.xlist(pt_list), Common.ylist(pt_list)
        spl = InterpolatedUnivariateSpline(xx, yy)
        return spl

    @classmethod
    def root(cls, spl, y, start, stop, scan_step=0.025):
        """计算样条曲线在y处于某个值时, 在[start, stop]范围内的交点
            :param spl: 样条函数
            :param y:
            :param start: 扫描的起点
            :param stop: 求交范围的终点
            :param scan_step: 扫描的精度, 默认0.05
            :return: 根的列表
            """
        out = []

        def func(x):
            return spl(x) - y

        # 在[start, stop]上搜索求根。
        for i in np.arange(start - 0.1, stop + 0.1, step=scan_step):
            if (func(i) <= 0 < func(i + scan_step)) or (func(i) >= 0 > func(i + scan_step)):
                x0, r = brenth(func, i, i + scan_step, full_output=True)
                x_val = float(x0)
                out.append((x_val, y), )
        # 当根的个数是技术的时候，分成1个或者3个及以上的情况来处理。
        if len(out) % 2 != 0 and len(out) > 1:
            tmp = []
            for p1, p2 in zip(out, out[1:]):
                if cls.distance(p1, p2) > 2.0:
                    tmp.extend([p1, p2])
            out = tmp[:]
        if len(out) == 1:
            out = []
        return out

    @classmethod
    def second_diff(cls, p1: Point2, p2: Point2, p3: Point2) -> float:
        """给定p1, p2, p3, x值依次增大, 求其二阶差商。
        :param p1:
        :param p2:
        :param p3:
        :return:
        """
        assert p1[0] < p2[0] < p3[0]
        alpha1 = (p2[1] - p1[1]) / (p2[0] - p1[0])
        alpha2 = (p3[1] - p1[1]) / (p3[0] - p1[0])
        _2d_alpha = (alpha2 - alpha1) / (p3[0] - p2[0])
        return _2d_alpha


class GenerateCoord(object):
    @classmethod
    def generate_xcoord(cls, spl, start, stop, step=1.0):
        out = []
        if start != ceil(start):
            start = ceil(start)
        else:
            start = start + step
        for x in np.arange(start, stop, step):
            y = float(spl(x))
            if y < 1.0:  # 过滤掉'孤儿点'
                continue
            pt_pair = [(x, y), (x, -y)]
            out.append(pt_pair)
        return out

    @classmethod
    def need_to_skip(cls, x1, x2):
        """本函数服务于generate_ycoord，用于改善求交中畸变的情况。
        :param x1:
        :param x2:
        :return:
        """
        assert x1 < x2
        # 调整点以避免8.99999和10.0000000003的情况
        t_x1 = x1 + 0.0001
        t_x2 = x2 - 0.0001
        if t_x1 > t_x2:
            return True
        elif ceil(t_x1) == floor(t_x2) or ceil(t_x1) > floor(t_x2):
            return True
        else:
            return False

    @classmethod
    def generate_ycoord(cls, spl, start, stop, step=1.0, *custom):
        """
        在[start, stop]范围内求交生成ycoord杆件布置。
        :param spl:
        :param start:
        :param stop:
        :param step:
        :param custom:
        :return:一个坐标对的列表。[[point1, point2], [point3, point4], ...]
        """
        assert len(custom) == 2 or len(custom) == 0
        if len(custom) == 2:
            x_c, y_c = custom
            out = [[(x_c, 0.0), (y_c, 0.0)], ]
        else:
            out = [[(start, 0.0), (stop, 0.0)], ]
            x_c, y_c = start, stop
        for y in np.arange(0.0 + step, stop, step):
            root_result = Common.root(spl, y, x_c, y_c, scan_step=0.005)
            if len(root_result) % 2 != 0:
                raise Exception("Wrong Root List %r" % root_result)
            if len(root_result) == 0:
                break
            for i in range(0, len(root_result), 2):
                # temp1 = root_result[i:i + 2]
                pt1, pt2 = root_result[i: i + 2]
                x1, y1 = pt1
                x2, y2 = pt2
                pt_pair1 = [(x1, y1), (x2, y2)]
                pt_pair2 = [(x1, -y1), (x2, -y2)]
                if cls.need_to_skip(x1, x2):  # skip the points which has only one cross node.
                    continue
                out.extend([pt_pair1, pt_pair2])
        return out

    @classmethod
    def get_cross_point(cls, x_pair, y_pair):
        x_pair.sort(key=itemgetter(1))
        y_pair.sort(key=itemgetter(0))
        x = x_pair[0][0]
        y = y_pair[0][1]
        if x_pair[0][1] < y < x_pair[1][1] and y_pair[0][0] < x < y_pair[1][0]:
            pt = (x, y)
            return pt
        else:
            return None

    @classmethod
    def generate_incoord(cls, xcoord, ycoord):
        incoord_set = set()
        for x_pair in xcoord:
            for y_pair in ycoord:
                pt = cls.get_cross_point(x_pair, y_pair)
                incoord_set.add(pt)
        if None in incoord_set:
            incoord_set.remove(None)
        out = list(incoord_set)
        return out


class GenerateAbaqusData(object):
    @classmethod
    def to_3d(cls, pt_list):
        """输入点的列表(x_coord或者in_coord之类), 增加z坐标=0.0的对应的三维点列表。
        :param pt_list:
        :rtype: list
        """
        data = list(chain(*pt_list))
        # 对于x_coord和y_coord生成的点对，需要再flatten一次
        if isinstance(data[0], list):
            data = list(chain(*data))
        out = []
        for x, y in zip(data[0::2], data[1::2]):
            pt = (x, y, 0.0)
            out.append(pt)
        return out

    @classmethod
    def to_json(cls, d_in, json_file_name,
                abaqus_dir, mdb_name, odb_name,
                iter_time, left_hang, left_hang_height,
                right_hang, right_hang_height,
                radius, thickness, elastic_modular, density,
                deformation_step_name,
                vector=(0, 0, 0),
                json_save_dir=os.getcwd()):
        """
        把平面布置的结果转换成abaqus前处理的文件。
        :param d_in: 平面布置的数据, 字典格式
        :param json_save_dir: 输出的json的保存路径
        :param json_file_name: json文件名
        :param abaqus_dir: abaqus工作目录
        :param mdb_name:
        :param odb_name:
        :param iter_time:
        :param left_hang:
        :param left_hang_height:
        :param right_hang:
        :param right_hang_height:
        :param vector:
        :return:
        """
        xcoord = d_in['xcoord']
        ycoord = d_in['ycoord']
        incoord = d_in['incoord']

        xcoord_3d = cls.to_3d(xcoord)
        ycoord_3d = cls.to_3d(ycoord)
        incoord_3d = cls.to_3d(incoord)

        d_out = dict()
        d_out['iter_time'] = iter_time
        d_out['abaqus_dir'] = abaqus_dir
        d_out['mdb_name'] = mdb_name
        d_out['odb_name'] = odb_name
        d_out['left_hang'] = left_hang
        d_out['left_hang_height'] = left_hang_height
        d_out['right_hang'] = right_hang
        d_out['right_hang_height'] = right_hang_height
        d_out['vector'] = vector
        d_out['xcoord'] = xcoord
        d_out['ycoord'] = ycoord
        d_out['incoord'] = incoord
        d_out['xcoord_3d'] = xcoord_3d
        d_out['ycoord_3d'] = ycoord_3d
        d_out['incoord_3d'] = incoord_3d

        d_out['deformation_step_name'] = deformation_step_name

        d_out['radius'] = radius
        d_out['thickness'] = thickness
        d_out['elastic_modular'] = elastic_modular
        d_out['density'] = density

        with open(json_save_dir + "/" + json_file_name, "w") as f:
            f.writelines(json.dumps(d_out, indent=4), )
        return d_out


class InitPlain(object):
    """
    作为utils的前端接口。
    输入点坐标列表，输出平面布置的json和示意图。
    """

    def __init__(self, pt_list):
        self.pt_list = sorted(pt_list, key=itemgetter(0))
        self.lb = self.pt_list[0][0]  # left_bound
        self.rb = self.pt_list[-1][0]  # right_bound
        self.spl = Common.get_spl(self.pt_list)

        self.xcoord = GenerateCoord.generate_xcoord(self.spl, self.lb, self.rb, 1.0)
        self.ycoord = GenerateCoord.generate_ycoord(self.spl, self.lb, self.rb, 1.0)
        self.incoord = GenerateCoord.generate_incoord(self.xcoord, self.ycoord)

    def to_json(self, file_name, save_path=os.getcwd()):
        d = {}
        d['xcoord'] = self.xcoord
        d['ycoord'] = self.ycoord
        d['incoord'] = self.incoord
        d['left_bound'] = self.lb
        d['right_bound'] = self.rb
        with open(save_path + "/" + file_name, "w") as f:
            f.writelines(json.dumps(d, indent=4))
        return d

    def plot_xy(self, file_name=None, save_path=os.getcwd()):
        """绘示意图。当file_name和save_path给了额外保存图像。
        :param file_name:
        :param save_path:
        :return:
        """
        fig = plt.figure(figsize=(15, 8))

        # 绘制控制点
        xx = Common.xlist(self.pt_list)
        yy = Common.ylist(self.pt_list)
        plt.plot(xx, yy, 'r^', markersize=16)

        # 绘制拟合的样条线
        xx = np.linspace(self.lb, self.rb, 300)
        yy = self.spl(xx)
        plt.plot(xx, yy, 'r--', linewidth=6)

        # 绘制边界点
        for pt_pair in self.xcoord + self.ycoord:
            xx = Common.xlist(pt_pair)
            yy = Common.ylist(pt_pair)
            plt.plot(xx, yy, linewidth=1.2)

        # 绘制内部点
        for x, y in self.incoord:
            plt.plot(x, y, 'ro', markersize=3.5)

        # 调整图像显示
        plt.xlim((self.lb, self.rb), )
        if file_name is not None:
            fig.savefig(save_path + "/" + file_name)
        plt.show()


if __name__ == '__main__':
    # test unit
    pass
