from odbAccess import openOdb
from abaqusConstants import *
import numpy as np
import os

# 设置包含 ODB 文件的目录
odb_dir = '.'  # 当前目录，或替换为你指定的目录路径
output_txt = '../output.txt'  # 输出路径，可根据需要修改

# # 清空旧结果（可选）
# with open(output_txt, 'w') as f:
#     f.write("应力提取结果如下：\n")

# 遍历目录下所有 .odb 文件
for filename in os.listdir(odb_dir):
    if filename.endswith('.odb'):
        odb_path = os.path.join(odb_dir, filename)
        try:
            odb = openOdb(path=odb_path)

            all_mises_values = []
            location_info = ""
            max_mises = -1e10

            for step_name, step in odb.steps.items():
                for frame in step.frames:
                    time = frame.frameValue
                    stress_field = frame.fieldOutputs['S']

                    for value in stress_field.values:
                        mises = value.mises
                        all_mises_values.append(mises)

                        if mises > max_mises:
                            max_mises = mises
                            location_info = (
                                f"Step: {step_name}, Frame: {time}, "
                                f"Element: {getattr(value, 'elementLabel', 'N/A')}, "
                                f"Integration Point: {value.integrationPoint}"
                            )

            if all_mises_values:
                q = 99.95
                percentile_95 = np.percentile(all_mises_values, q)

                output_line = (
                    f"[{filename}] 最大Von Mises应力: {max_mises:.2f} MPa, "
                    f"{q}%分位应力: {percentile_95:.2f} MPa, "
                    f"位置: {location_info}"
                )
            else:
                output_line = f"[{filename}] 无有效应力数据"

            print(output_line)

            with open(output_txt, 'a') as f:
                f.write(output_line + "\n")

            odb.close()
        except Exception as e:
            error_msg = f"[{filename}] 处理失败: {str(e)}"
            print(error_msg)
            with open(output_txt, 'a') as f:
                f.write(error_msg + "\n")
