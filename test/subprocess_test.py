import subprocess
from subprocess import PIPE

# child = subprocess.Popen(["ping", "www.baidu.com"], stdout=PIPE)
# res = child.communicate()
# for line in res:
#     try:
#         line = line.decode("gbk")
#         print line
#     except Exception as e:
#         print e, line



child = subprocess.Popen(["C:/SIMULIA/Abaqus/6.14-2/code/bin/abq6142.exe", "cae"], stdout=PIPE)
res = child.communicate()
for line in res:
    try:
        line = line.decode("gbk")
        print line
    except Exception as e:
        print e, line