# coding=utf-8
import json
from math import sqrt
from operator import itemgetter
from typing import List, Tuple, Union

import matplotlib.pyplot as plt
from numpy import std

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]
ResArr = Tuple[float, float, float, float, float, float]

Point = Union[Tuple, List]


def avg_err(points: list) -> (float, float):
    """计算边界点的平均值和标准差
    :param points:
    :return:
    """
    dis = [p[-1] for p in points]
    avg = (sum(dis) + 0.0) / len(dis)
    stderr = std(dis)
    return avg, stderr


class Distance(object):
    @classmethod
    def __2or3(cls, p1: Point, p2: Point) -> int:
        """判断2d点或者3d点，若纬度不对抛异常
        :param p1:
        :param p2:
        :return:
        """
        if len(p1) == len(p2) == 2:
            return 2
        elif len(p1) == len(p2) == 3:
            return 3
        else:
            raise Exception("计算距离函数的点维度不对!" + "p1=%s p2=%s" % (p1, p2))

    @classmethod
    def abs(cls, p1: Point, p2: Point) -> float:
        """计算两点间的曼哈顿距离
            :param p1:
            :param p2:
            :return:
            """
        if cls.__2or3(p1, p2) == 2:
            return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
        else:
            return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) + abs(p1[2] - p2[2])

    @classmethod
    def euclidean(cls, p1: Point, p2: Point) -> float:
        """计算两点间的欧几里德距离
        :param p1:
        :param p2:
        :return:
        """
        if cls.__2or3(p1, p2) == 2:
            x_2 = p1[0] ** 2 + p2[0] ** 2
            y_2 = p1[1] ** 2 + p2[1] ** 2
            return sqrt(x_2 + y_2)
        else:
            x_2 = p1[0] ** 2 + p2[0] ** 2
            y_2 = p1[1] ** 2 + p2[1] ** 2
            z_2 = p1[2] ** 2 + p2[2] ** 2
            return sqrt(x_2 + y_2 + z_2)


class Iteration(object):
    """
    思路：
    先找出所有边界点对应的相邻的内部点，形成点对。 -> get_b_in_pair
    然后根据一次拟合，计算如果要把边界点调整到平均值，则空间点所在的位置。 -> func1
    根据点对的相对空间位置和平面位置，以及调整的方向，得到新的平面点的坐标 -> func2
    """

    @classmethod
    def get_b_in_pairs(cls, pts_b, pts_in):
        """找出所有边界点(pts_b)对应的内部点(pts_in)
        :param pts_b:
        :param pts_in:
        :return: 点对(pt_pair)的列表
        """
        pairs = []
        for p_b in pts_b:
            for p_in in pts_in:
                p1, p2 = p_b[:3], p_in[:3]
                if Distance.abs(p1, p2) <= 1.0:
                    pairs.append((p_b, p_in))
        return pairs

    @classmethod
    def relation(cls, p_b, p_in, accuracy=0.0001):
        """判断p_b和p_in之间的关系, 若平行于X轴则输出x, 平行于Y轴输出y.
        :param p_b:
        :param p_in:
        :param accuracy:
        :return:
        """
        if abs(p_b[0] - p_in[0]) < accuracy:
            return 'y'
        elif abs(p_b[1] - p_in[1]) < accuracy:
            return 'x'
        else:
            raise Exception("错误的点对!" + "p_b=%s, p_in=%s" % (p_b, p_in))

    # TODO: 构造avg_space_point单独的单元测试，覆盖四个象限的情况
    @classmethod
    def avg_space_point(cls, p_b: ResArr, p_in: ResArr, avg_z: float):
        """由边界点和其相邻内部点的空间位置得到的直线，计算当位移等于avg的时候的空间点。
        :param p_b:
        :param p_in:
        :param avg_z:
        :return:
        """
        relation = cls.relation(p_b, p_in)
        # TODO: 处理delta_z太小的情况,可以考虑在生成新的差值曲线时不考虑这个点
        delta_z = p_b[5] - p_in[5]
        if relation == 'x':  # 两点平行于x轴
            delta_x = p_b[3] - p_in[3]
            avg_x = (avg_z - p_b[5]) * delta_x / delta_z + p_b[3]
            avg_space_pt = (avg_x, p_b[4], avg_z)
        else:
            assert relation == 'y'  # 两点平行于y轴
            delta_y = p_b[4] - p_in[4]
            avg_y = (avg_z - p_b[5]) * delta_y / delta_z + p_b[4]
            avg_space_pt = (p_b[3], avg_y, avg_z)
        return avg_space_pt

    @classmethod
    def adjust(cls, p_b: ResArr, p_in: ResArr, avg_z: float) -> Point2:
        """计算avg所在空间点和目前边界点的距离, 根据当前p_b和临近p_in计算新的p_b所在位置.
        :param p_b:
        :param p_in:
        :param avg_z:
        :return:
        """
        relation = cls.relation(p_b, p_in)
        avg_point = cls.avg_space_point(p_b, p_in, avg_z)
        dis = Distance.euclidean(p_b[3:], avg_point)
        if relation == 'x':
            if p_b[0] < p_in[0]:
                new_x = p_b[0] - dis
            else:
                new_x = p_b[0] + dis
            out = (new_x, p_b[1])
        else:
            if p_b[1] < p_in[1]:
                new_y = p_b[1] - dis
            else:
                new_y = p_b[1] + dis
            out = (p_b[0], new_y)
        return out

    def __solve(self):
        pairs = self.get_b_in_pairs(self.bound_pts, self.inner_pts)
        new_points = dict()
        for p_b, p_in in pairs:
            p_new = self.adjust(p_b, p_in, self.avg_z)
            new_points[tuple(p_b)] = p_new
        return new_points

    def plot(self):
        """
        :return:
        """
        fig = plt.figure(figsize=(15, 8))
        for pt_old, pt_new in self.new_points.items():
            xx = [pt_old[0], pt_new[0]]
            yy = [pt_old[1], pt_new[1]]
            plt.plot(xx, yy)
        plt.show()

    def __init__(self, d_in):
        self.bound_pts = sorted(d_in['bound_pts'], key=itemgetter(0))
        self.inner_pts = sorted(d_in['inner_pts'], key=itemgetter(0))
        self.avg_z, self.stderr = avg_err(self.bound_pts)
        self.new_points = self.__solve()


if __name__ == '__main__':
    data_path = "E:/Abaqusdir/auto/output"
    file_name = "pm1508.json"
    with open(data_path + "/" + file_name) as f:
        d = json.load(f)

    iter = Iteration(d)
    iter.plot()
