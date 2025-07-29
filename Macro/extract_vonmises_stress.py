from odbAccess import openOdb
from abaqusConstants import *

odb_path = 'ZZ35.odb'  # <-- 请修改为你的实际文件名
odb = openOdb(path=odb_path)

overall_max_mises = -1e10
location_info = ""

# 遍历每个步骤
for step_name, step in odb.steps.items():
    print(f"\n>>> Step: {step_name}")
    for frame in step.frames:
        time = frame.frameValue
        stress_field = frame.fieldOutputs['S']  # 应力场输出

        max_mises_in_frame = -1e10

        for value in stress_field.values:
            mises = value.mises
            if mises > max_mises_in_frame:
                max_mises_in_frame = mises
            if mises > overall_max_mises:
                overall_max_mises = mises
                location_info = (
                    f"Step: {step_name}, Frame: {time}, "
                    f"Element: {getattr(value, 'elementLabel', 'N/A')}, "
                    f"Integration Point: {value.integrationPoint}"
                )

        print(f"  Frame {time:.3f}: 最大Von Mises = {max_mises_in_frame:.2f} MPa")

print("\n==== 最终结果 ====")
print(f"最大Von Mises 应力：{overall_max_mises:.2f} MPa")
with open("../output.txt",'a') as f:
    f.write(f"{overall_max_mises}\n")
print(f"位置：{location_info}")

odb.close()
