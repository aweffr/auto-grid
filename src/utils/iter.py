# coding=utf-8
import json

data_path = "E:/Abaqusdir/auto/output"
file_name = "pm1508.json"
with open(data_path + "/" + file_name) as f:
    d = json.load(f)

