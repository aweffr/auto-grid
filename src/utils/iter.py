# coding=utf-8
import json
from math import sqrt
from operator import itemgetter

import matplotlib.pyplot as plt
from numpy import std
from scipy.interpolate import UnivariateSpline

from src.utils.my_types import Point, Point2, OdbArr, IterResult
from src.utils.utils import InitPlain


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
            x_2 = (p1[0] - p2[0]) ** 2
            y_2 = (p1[1] - p2[1]) ** 2
            return sqrt(x_2 + y_2)
        else:
            x_2 = (p1[0] - p2[0]) ** 2
            y_2 = (p1[1] - p2[1]) ** 2
            z_2 = (p1[2] - p2[2]) ** 2
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
    def avg_space_point(cls, p_b: OdbArr, p_in: OdbArr, avg_z: float):
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
    def adjust_by_k(cls, p_b: OdbArr, p_in: OdbArr, avg_z: float, factor: float = 1.0) -> Point2:
        """计算avg所在空间点和目前边界点的距离, 根据当前p_b和临近p_in计算新的p_b所在位置.
        :param p_b:
        :param p_in:
        :param avg_z:
        :param factor: 步进速率
        :return:
        """
        assert factor > 0, "步进速率必须>0"
        relation = cls.relation(p_b, p_in)
        avg_point = cls.avg_space_point(p_b, p_in, avg_z)
        # print("Now adjust p_b=%s, p_in=%s, avg_point=%s" % (p_b, p_in, avg_point))
        dis = Distance.euclidean(p_b[3:], avg_point)
        if p_b[-1] > avg_z:
            adj_val = dis * factor
        else:
            adj_val = -dis * factor
        if relation == 'x':
            if p_b[0] < p_in[0]:
                new_x = p_b[0] - adj_val
            else:
                new_x = p_b[0] + adj_val
            out = (new_x, p_b[1])
        else:
            if p_b[1] < p_in[1]:
                new_y = p_b[1] - adj_val
            else:
                new_y = p_b[1] + adj_val
            out = (p_b[0], new_y)
        return out

    @classmethod
    def adjust_by_z(cls, p_b: OdbArr, p_in: OdbArr, avg_z: float, factor: float = 1.0) -> Point2:
        """计算avg和当前点z坐标的高差，然后以此高差结合p_b和p_in的关系计算新的p_b所在位置。
        :param p_b:
        :param p_in:
        :param avg_z:
        :param factor:
        :return:
        """
        assert factor > 0, "步进速率必须>0"
        relation = cls.relation(p_b, p_in)
        diff_h = p_b[-1] - avg_z
        adj_val = diff_h * factor
        if relation == 'x':
            if p_b[0] < p_in[0]:
                new_x = p_b[0] - adj_val
            else:
                new_x = p_b[0] + adj_val
            out = (new_x, p_b[1])
        else:
            if p_b[1] < p_in[1]:
                new_y = p_b[1] - adj_val
            else:
                new_y = p_b[1] + adj_val
            out = (p_b[0], new_y)
        return out

    @classmethod
    def smooth(cls, iter_result: IterResult):
        """
        先用smooth过的样条线拟合这些点，对于离散度大的进行删除。
        :param iter_result:
        :return:
        """
        raw_pts = iter_result.values()
        new_pts = []
        # 只取大于等于零的点
        raw_pts = [p for p in raw_pts if p[1] >= 0]
        raw_pts.sort(key=itemgetter(0))
        w = [1 for p in raw_pts]
        w[0], w[-1] = 100, 100
        spl = UnivariateSpline([p[0] for p in raw_pts], [p[1] for p in raw_pts], w=w, s=3)
        excluded_pts = set()
        for p in raw_pts:
            if abs(p[1] - spl(p[0])) > 0.3:
                excluded_pts.add(p)
        for p in raw_pts:
            if p not in excluded_pts:
                new_pts.append(p)
        return new_pts

    def __solve(self) -> IterResult:
        pairs = self.get_b_in_pairs(self.bound_pts, self.inner_pts)
        new_points = dict()
        for p_b, p_in in pairs:
            p_new = self.adjust_by_z(p_b, p_in, self.avg_z, factor=self.factor)
            new_points[tuple(p_b)] = p_new
        return new_points

    def plot_raw_result(self):
        """
        :return:
        """
        fig = plt.figure(figsize=(15, 8))
        for pt_old, pt_new in self.raw_points.items():
            # xx = [pt_old[0], pt_new[0]]
            # yy = [pt_old[1], pt_new[1]]
            # plt.plot(xx, yy)
            plt.plot(pt_old[0], pt_old[1], "bo")
            plt.plot(pt_new[0], pt_new[1], "ro")
        # plt.show()
        for p in self.new_points:
            plt.plot(p[0], p[1], 'g^')
        plt.show()

    def plot_new_result(self):
        """
        :return:
        """
        for p in self.new_points:
            plt.plot(p[0], p[1], 'ro')
        plt.show()

    def generate_new_plain(self):
        new_plain = InitPlain(self.new_points)
        return new_plain

    def __init__(self, d_in, factor):
        self.factor = factor
        self.bound_pts = sorted(d_in['bound_pts'], key=itemgetter(0))
        self.inner_pts = sorted(d_in['inner_pts'], key=itemgetter(0))
        self.avg_z, self.stderr = avg_err(self.bound_pts)
        self.raw_points = self.__solve()
        self.new_points = self.smooth(self.raw_points)


if __name__ == '__main__':
    data_path = "E:/Abaqusdir/auto/output"
    file_name = "pm1508.json"
    with open(data_path + "/" + file_name) as f:
        d = json.load(f)

    iter = Iteration(d)
    iter.plot_raw_result()
    iter.plot_new_result()
