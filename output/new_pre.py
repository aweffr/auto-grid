# -*- coding: utf-8 -*-

from part import *
from material import *
from section import *
from optimization import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
import math
import os
import shelve
import argparse
import json

# parser = argparse.ArgumentParser()
# parser.add_argument("json_path")
# args = parser.parse_args()

json_file = os.environ.get("JSON", failobj="test_init.json")

with open(json_file, "r") as f:
    d = json.load(f)

# f = shelve.open('D:/abaqus_execpy/_sym/model-files/sym-40-3.dat')

# 保存的文件名，提交的计算作业名
mdb_name = str(d['mdb_name'])
odb_name = str(d['odb_name'])
abaqus_dir = d['abaqus_dir']
os.chdir(abaqus_dir)

iter_time = d["iter_time"]

# 起吊点高度和位置
left_hang_height = d['left_hang_height']
left_hang = d['left_hang']
right_hang_height = d['right_hang_height']
right_hang = d['right_hang']

xcoord =  d['xcoord']
ycoord =  d['ycoord']
incoord = d['incoord']
xcoord_3d =  d['xcoord_3d']
ycoord_3d =  d['ycoord_3d']
incoord_3d = d['incoord_3d']
vector = d['vector']

radius = d['radius']
thickness = d['thickness']
elastic_modular = d['elastic_modular']
density = d['density']

#--------------------Abaqus PDE Process----------------------------

def distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


# 创建模型，命名为Model A
myModel = mdb.Model(name=mdb_name)

# 创建草图图形，命名为Model A，令mySketchA作为对象入口
mySketchA = myModel.ConstrainedSketch(name='Sketch A', sheetSize=200.0)

# 连接由X轴的坐标控制的点
for p1, p2 in xcoord:
    mySketchA.Line(point1=p1, point2=p2)

# 创建草图图形，命名为Model B，令mySketchB作为对象入口
mySketchB = myModel.ConstrainedSketch(name='Sketch B', sheetSize=200.0)

# 连接由Y轴的坐标控制的点，读取lst2中的坐标
for p1, p2 in ycoord:
    mySketchB.Line(point1=p1, point2=p2)


# 创建PartA和PartB, PartA对应lst1, PartB对应lst2
myPartA = myModel.Part(name='Part A', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPartA.BaseWire(sketch=mySketchA)
myPartB = myModel.Part(name='Part B', dimensionality=THREE_D, type=DEFORMABLE_BODY)
myPartB.BaseWire(sketch=mySketchB)

# 创建分割点
for coord in incoord_3d:
    edgeA = myPartA.edges.findAt(coord,)
    edgeB = myPartB.edges.findAt(coord,)
    if edgeA != None:
        myPartA.PartitionEdgeByPoint(edge=edgeA, point=coord)
    if edgeB != None:
        myPartB.PartitionEdgeByPoint(edge=edgeB, point=coord)


# 模型空间组装 Assembly
myAssembly = mdb.models[mdb_name].rootAssembly

# 定义全局坐标为直角坐标系
myAssembly.DatumCsysByDefault(CARTESIAN)

# 引入PartA和PartB
Instance_A = myAssembly.Instance(dependent=ON, name='PartA', part=myPartA)
Instance_B = myAssembly.Instance(dependent=ON, name='PartB', part=myPartB)

# for coord in gravityCentre:
#     myAssembly.DatumPointByCoordinate(coords=coord)

def setMaker(coord_data, targetInstance, setName='default'):
    # 定义点集合，输入格式为： 点坐标集合， 目标实体， 输出set名称
    setForAbaqus = []
    for tup in coord_data:
    # findAt((tup,),)
        setForAbaqus.append(
            targetInstance.vertices.findAt((tup,),)
            )
    return myAssembly.Set(name=setName, vertices=setForAbaqus)

set_PartA_InnerPoints = setMaker(incoord_3d, Instance_A, 'PartA_Inner')
set_PartB_InnerPoints = setMaker(incoord_3d, Instance_B, 'PartB_Inner')
set_PartA_BoundaryPoints = setMaker(xcoord_3d, Instance_A, 'PartA_Boundary')
set_PartB_BoundaryPoints = setMaker(ycoord_3d, Instance_B, 'PartB_Boundary')
setForConnector = myAssembly.SetByBoolean(
    name='AllBoundPoints',
    sets=[set_PartA_BoundaryPoints, set_PartB_BoundaryPoints],
    operation=UNION,
    )

# 沿向量vect平移PartA，用于考虑连接件长度
myAssembly.translate(instanceList=('PartA',), vector=vector)

# 创建连接件的耦合单元
myModel.Coupling(controlPoint=set_PartB_InnerPoints,
                 couplingType=KINEMATIC,
                 influenceRadius=0.05,
                 localCsys=None,
                 name='Couple',
                 surface=set_PartA_InnerPoints,
                 u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=OFF)

# 赋予材料属性及截面
myMaterial = myModel.Material(name='FRP')
myMaterial.Elastic(table=((elastic_modular, 0.28), ))
myMaterial.Density(table=((density, ), ))
myModel.PipeProfile(name='P1', r=radius, t=thickness)
myModel.BeamSection(consistentMassMatrix=False,
                    integration=DURING_ANALYSIS,
                    material='FRP',
                    name='Pipe',
                    poissonRatio=0.0,
                    profile='P1',
                    temperatureVar=LINEAR)

# 将截面赋予到Part上
partSetB = myPartB.Set(
    edges=myPartB.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0),
    name='PartB')

myPartB.SectionAssignment(
    offset=0.0,
    offsetField='',
    offsetType=MIDDLE_SURFACE,
    region=partSetB,
    sectionName='Pipe',
    thicknessAssignment=FROM_SECTION)

myPartB.assignBeamSectionOrientation(
    method=N1_COSINES,
    n1=(0.0, 0.0, -1.0),
    region=partSetB)

partSetA= myPartA.Set(
    edges=myPartA.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0),
    name='PartA')

myPartA.SectionAssignment(
    offset=0.0,
    offsetField='',
    offsetType=MIDDLE_SURFACE,
    region=partSetA,
    sectionName='Pipe',
    thicknessAssignment=FROM_SECTION)

myPartA.assignBeamSectionOrientation(
    method=N1_COSINES,
    n1=(0.0, 0.0, -1.0),
    region=partSetA)

# Meshing
myPartA.seedPart(deviationFactor=1, minSizeFactor=0.1, size=1)
myPartA.generateMesh()

myPartB.seedPart(deviationFactor=1, minSizeFactor=0.1, size=1)
myPartB.generateMesh()

# Step,Load
Step_1 = myModel.StaticStep(
    initialInc=0.00025, 
    maxInc=0.1,
    minInc=1e-12,
    maxNumInc=0X7FFFFFFF,
    name='Step-1',
    previous='Initial',
    nlgeom=ON,
    solutionTechnique=FULL_NEWTON)
# Step_1.setValues(initialInc=0.00025,
#                  maxInc=0.1,
#                  maxNumInc=0X7FFFFFFF,
#                  minInc=1e-12,
#                  nlgeom=ON,
#                  solutionTechnique=FULL_NEWTON,)

set_Whole = myAssembly.Set(
    edges=Instance_A.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0)+\
    Instance_B.edges.getByBoundingBox(xMin=-60.0,xMax=60.0,yMin=-60.0,yMax=60.0,zMin=-60.0,zMax=60.0),
    name='Whole')
myModel.Gravity(
    comp3=-9.8,
    createStepName='Step-1',
    name='Gravity',
    distributionType=UNIFORM,
    field='')

# For multi hanging points, set the Reference Points.
# According to the API, the reference of REFERENCEPOINTs need to be redefined.
hang_height = 5.0
left_reference_coord = (left_hang, 0.0, hang_height)
right_reference_coord = (right_hang, 0.0, hang_height)
rerferencePoint1 = myAssembly.ReferencePoint(point=left_reference_coord,)
rerferencePoint1 = myAssembly.referencePoints.findAt(left_reference_coord,)
rerferencePoint2 = myAssembly.ReferencePoint(point=right_reference_coord,)
rerferencePoint2 = myAssembly.referencePoints.findAt(right_reference_coord,)

verticesLeft =  Instance_B.vertices.getByBoundingBox(xMin=left_hang-0.1, xMax=left_hang+0.1, yMin=-2.1, yMax=-1.9, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=left_hang-0.1, xMax=left_hang+0.1, yMin=1.9, yMax=2.1, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=left_hang-2.1, xMax=left_hang-1.9, yMin=-0.1, yMax=0.1, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=left_hang+1.9, xMax=left_hang+2.1, yMin=-0.1, yMax=0.1, zMin=-0.1, zMax=0.1)

verticesRight = Instance_B.vertices.getByBoundingBox(xMin=right_hang-0.1, xMax=right_hang+0.1, yMin=-2.1, yMax=-1.9, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=right_hang-0.1, xMax=right_hang+0.1, yMin=1.9, yMax=2.1, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=right_hang-2.1, xMax=right_hang-1.9, yMin=-0.1, yMax=0.1, zMin=-0.1, zMax=0.1) + \
                Instance_B.vertices.getByBoundingBox(xMin=right_hang+1.9, xMax=right_hang+2.1, yMin=-0.1, yMax=0.1, zMin=-0.1, zMax=0.1)

set_loadLeft = myAssembly.Set(
    name='Set-loadLeft',
    referencePoints=(rerferencePoint1,),
    )
set_loadRight = myAssembly.Set(
    name='Set-loadRight',
    referencePoints=(rerferencePoint2,),
    )
set_loadMiddle = myAssembly.Set(
    name='Set-loadMiddle',
    vertices=Instance_B.vertices.getByBoundingBox(xMin=23.9,xMax=24.1,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
    )
set_symBoundCondition = myAssembly.Set(
    name='Set-symBoundCondition',
    vertices=Instance_B.vertices.getByBoundingBox(xMin=-10.0,xMax=60.0,yMin=-0.1,yMax=0.1,zMin=-0.1,zMax=0.1)
)

# 创建MPC连接
myMPC_Properity = myModel.MPCSection(mpcType=LINK_MPC, name='ConnSect-Link', userMode=DOF_MODE, userType=0)

for vertix in verticesLeft:
    myAssembly.WirePolyLine(
        points=((rerferencePoint1, vertix),),
        meshable=OFF
    )
for vertix in verticesRight:
    myAssembly.WirePolyLine(
        points=((rerferencePoint2, vertix),),
        meshable=OFF
    )

setLinkLine = myAssembly.Set(
    edges=myAssembly.edges,
    name='MPCwires',
    )
myMPC_Assignment = myAssembly.SectionAssignment(
    region=setLinkLine,
    sectionName='ConnSect-Link'
    )

myModel.DisplacementBC(amplitude=UNSET,
                       createStepName='Step-1',
                       distributionType=UNIFORM,
                       fieldName='',
                       fixed=OFF,
                       localCsys=None,
                       name='set_SymBoundCondition',
                       region=set_symBoundCondition,
                       u1=UNSET, u2=0.0, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

myModel.DisplacementBC(amplitude=UNSET,
                       createStepName='Step-1',
                       distributionType=UNIFORM,
                       fieldName='',
                       fixed=OFF,
                       localCsys=None,
                       name='BC-Left',
                       region=set_loadLeft,
                       u1=UNSET, u2=0.0, u3=left_hang_height, ur1=0.0, ur2=UNSET, ur3=0.0)

myModel.DisplacementBC(amplitude=UNSET,
                       createStepName='Step-1',
                       distributionType=UNIFORM,
                       fieldName='',
                       fixed=OFF,
                       localCsys=None,
                       name='BC-Right',
                       region=set_loadRight,
                       u1=UNSET, u2=0.0, u3=right_hang_height, ur1=0.0, ur2=UNSET, ur3=0.0)

myModel.DisplacementBC(amplitude=UNSET,
                       createStepName='Step-1',
                       distributionType=UNIFORM,
                       fieldName='',
                       fixed=OFF,
                       localCsys=None,
                       name='BC-Middle',
                       region=set_loadMiddle,
                       u1=0.0, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

submitJob = mdb.Job(atTime=None,
        name=odb_name,
        contactPrint=OFF,
        description='Iteration time: %d'%iter_time,
        echoPrint=ON,
        explicitPrecision=SINGLE,
        getMemoryFromAnalysis=True,
        historyPrint=OFF,
        memory=95, memoryUnits=PERCENTAGE,
        model=mdb_name, 
        modelPrint=OFF,
        multiprocessingMode=DEFAULT,
        nodalOutputPrecision=SINGLE,
        numCpus=4, numDomains=8, numGPUs=0, queue=None,
        scratch='',
        type=ANALYSIS,
        userSubroutine='',
        waitHours=0, waitMinutes=0)

print "Now Job created!"
submitJob.submit(consistencyChecking=OFF)
print "Now Job submitted!"
mdb.saveAs(pathName=mdb_name)