# -*- coding:utf-8 -*-
# odbProcessor.py
# 本脚本用于得到边界点和内部点的后处理（位移）数据。
# 对于边界点，数据格式为np.array(), (original, original, deformed)
# 对于内部点，数序格式为np.array(), (deformed, deformed, deformed)

import shelve
import json
from odbAccess import *
from numpy import array, array2string, std, zeros
import os


def isSamePoint(point1, point2, err=0.0002):
    # 输入两个点，判断两个点平面上是不是同一个点
    if abs(point1[0] - point2[0]) + abs(point1[1] - point2[1]) < err:
        return True
    else:
        return False


def isSetPoints(inputPoint, innerPointLst, err=0.0002):
    # point -> 判断改点算不算内部点
    # innerPointLst -> 模型文件中内部点的坐标
    for point in innerPointLst:
        if isSamePoint(inputPoint, point):
            return True
    return False


def stderr(pointlst):
    # To compute the standard error of z direction deformation.
    temp_z = []
    for point in pointlst:
        temp_z.append(point[5])
    stderr = std(temp_z)
    return stderr


def get_node_deformation(odb, d_in, step_name):
    """
    :param odb打开的odb对象
    """

    # 起吊点高度和位置
    mdb_name = str(d_in['mdb_name'])
    odb_name = str(d_in['odb_name'])
    left_hang_height = d_in['left_hang_height']
    left_hang = d_in['left_hang']
    right_hang_height = d_in['right_hang_height']
    right_hang = d_in['right_hang']

    xcoord = d_in['xcoord']
    ycoord = d_in['ycoord']
    incoord = d_in['incoord']
    xcoord_3d = d_in['xcoord_3d']
    ycoord_3d = d_in['ycoord_3d']
    incoord_3d = d_in['incoord_3d']
    vector = d_in['vector']

    radius = d_in['radius']
    thickness = d_in['thickness']
    elastic_modular = d_in['elastic_modular']
    density = d_in['density']

    json_save_dir = d_in['json_save_dir']
    res_file_prefix = d_in['res_file_prefix']

    # abaqus中的API模块，提取最终变形的data.
    final_frame = odb.steps[step_name].frames[-1]

    d = dict()

    innerPointsDeformed = []
    boundPointsDeformed = []

    for value in final_frame.fieldOutputs['U'].values:
        # 当模型中存在connector时该instance为None,需要跳过
        if value.instance == None:
            continue
        nodeLabel = value.nodeLabel
        checkLabel = value.instance.nodes[value.nodeLabel - 1].label
        if nodeLabel == checkLabel:
            deformationVector = array(value.data)
            orignalCoordinate = array(
                value.instance.nodes[value.nodeLabel - 1].coordinates)
            # 此处判断该点是否为边界点
            if isSetPoints(orignalCoordinate, xcoord_3d) or isSetPoints(orignalCoordinate, ycoord_3d):
                tempArray = zeros(6, float)
                tempArray[:3] = orignalCoordinate
                tempArray[3:] = orignalCoordinate + deformationVector
                # To Json
                tempArray = list(tempArray)
                boundPointsDeformed.append(tempArray)
            elif (orignalCoordinate[0] % 1.0 == 0 and orignalCoordinate[1] % 1.0 == 0) \
                    and isSetPoints(orignalCoordinate, incoord_3d):
                tempArray = zeros(6, float)
                tempArray[:3] = orignalCoordinate
                tempArray[3:] = orignalCoordinate + deformationVector
                # To Json
                tempArray = list(tempArray)
                innerPointsDeformed.append(tempArray)
        else:
            print('Wrong point, Label is %d' % nodeLabel)

    d['bound_pts'] = boundPointsDeformed
    d['inner_pts'] = innerPointsDeformed
    d['bound_stderr'] = stderr(boundPointsDeformed)

    # with open(odb_name + ".json", "w") as f:
    #     f.writelines(json.dumps(d, indent=4))

    result_file = json_save_dir + "/" + res_file_prefix + odb_name + ".json"
    with open(result_file, "w") as f:
        f.writelines(json.dumps(d, indent=4))

    print("Finished!")


if __name__ == '__main__':
    json_file = os.environ.get("JSON", failobj="test_init.json")
    with open(json_file, "r") as f:
        d = json.load(f)

    # 保存的文件名，提交的计算作业名
    mdb_name = str(d['mdb_name'])
    odb_name = str(d['odb_name'])
    abaqus_dir = d['abaqus_dir']
    deformation_step_name = str(d['deformation_step_name'])
    os.chdir(abaqus_dir)

    iter_time = d["iter_time"]

    odb = openOdb(path=odb_name + ".odb")
    try:
        get_node_deformation(odb=odb, d_in=d, step_name=deformation_step_name)
    except Exception as e:
        print(e)
    finally:
        odb.close()
