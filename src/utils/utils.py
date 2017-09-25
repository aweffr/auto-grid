# -*- coding:utf-8 -*-

import os
import matplotlib.pyplot as plt
import numpy as np
from math import floor, ceil
from scipy.optimize import brenth
from operator import itemgetter
from scipy.interpolate import InterpolatedUnivariateSpline
import json

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
        return map(lambda x: x[0], inlst)

    @staticmethod
    def ylist(inlst):
        # inlst format same as xlist
        # out format: [b1, b2, b3, ..., bn]
        return map(lambda x: x[1], inlst)

    @staticmethod
    def zlist(inlst):
        return map(lambda x: x[2], inlst)

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

    @staticmethod
    def root(spl, y, start, stop, scan_step=0.025):
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
                if Common.distance(p1, p2) > 2.0:
                    tmp.extend([p1, p2])
            out = tmp[:]
        if len(out) == 1:
            out = []
        return out


def generate_xcoord(spl, start, stop, step=1.0):
    out = []
    for x in np.arange(start + step, stop, step):
        y = float(spl(x))
        pt_pair = [(x, y), (x, -y)]
        out.append(pt_pair)
    return out


def need_to_skip(x1, x2):
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
    elif ceil(t_x1) == floor(t_x2):
        return True
    else:
        return False


def generate_ycoord(spl, start, stop, step=1.0, *custom):
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
    for y in np.arange(start + step, stop, step):
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
            if need_to_skip(x1, x2):  # skip the points which has only one cross node.
                continue
            out.extend([pt_pair1, pt_pair2])
    return out


def get_cross_point(x_pair, y_pair):
    x_pair.sort(key=itemgetter(1))
    y_pair.sort(key=itemgetter(0))
    x = x_pair[0][0]
    y = y_pair[0][1]
    if x_pair[0][1] < y < x_pair[1][1] and y_pair[0][0] < x < y_pair[1][0]:
        pt = (x, y)
        return pt
    else:
        return None


def generate_incoord(xcoord, ycoord):
    incoord_set = set()
    for x_pair in xcoord:
        for y_pair in ycoord:
            pt = get_cross_point(x_pair, y_pair)
            incoord_set.add(pt)
    incoord_set.remove(None)
    out = list(incoord_set)
    return out


def to_3d_xy(pointlst):
    # Input format:[ [(a1, b1), (a2, b2)],
    #                [(a3, b3), (a4, b4)],
    #                ......
    #                [......,   (an, bn)] ]
    # Output format:[(a1, b1, 0.0), (a2, b2, 0.0), ..., (an, bn, 0.0)]
    out = []
    for lst in pointlst:
        for x, y in lst:
            out.append((x, y, 0.0), )
    return out


def to_3d_in(pointlst):
    # Input format:[ (a1, b1), (a2, b2), ..., (an, bn)]
    # Output format:[ (a1, b1, 0.0), (a2, b2, 0.0), ..., (an, bn, 0.0)]
    out = []
    for x, y in pointlst:
        out.append((x, y, 0.0))
    return out


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

        self.xcoord = generate_xcoord(self.spl, self.lb, self.rb, 1.0)
        self.ycoord = generate_ycoord(self.spl, self.lb, self.rb, 1.0)
        self.incoord = generate_incoord(self.xcoord, self.ycoord)

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
        fig = plt.figure(figsize=(15, 8))
        xx = Common.xlist(self.pt_list)
        yy = Common.ylist(self.pt_list)
        plt.plot(xx, yy, 'r^', markersize=16)
        xx = np.linspace(self.lb, self.rb, 300)
        yy = self.spl(xx)
        plt.plot(xx, yy, 'r--', linewidth=6)
        for pt_pair in self.xcoord + self.ycoord:
            xx = Common.xlist(pt_pair)
            yy = Common.ylist(pt_pair)
            plt.plot(xx, yy, linewidth=1.2)
        for x, y in self.incoord:
            plt.plot(x, y, 'ro', markersize=3.5)
        plt.xlim((self.lb, self.rb), )
        if file_name is not None:
            fig.savefig(save_path + "/" + file_name)
        plt.show()


if __name__ == '__main__':
    # test unit
    pass
