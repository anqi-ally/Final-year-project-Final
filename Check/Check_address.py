import pyvisa

rm = pyvisa.ResourceManager()
resources = rm.list_resources()

print("已连接的设备资源地址:")
if resources:
    for resource in resources:
        print(resource)
else:
    print("未检测到任何 VISA 设备，请检查连接。")
