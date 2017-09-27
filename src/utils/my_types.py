from typing import List, Tuple, Union, Dict

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]
OdbArr = Tuple[float, float, float, float, float, float]

Point = Union[Tuple, List]

IterResult = Dict[OdbArr, Point2]
