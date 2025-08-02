from odbAccess import openOdb
from abaqusConstants import *
import numpy as np
import os

# 指定 ODB 目录与输出文件路径
odb_dir = '.'
output_txt = '../output.txt'

# 清空旧输出
with open(output_txt, 'w') as f:
    f.write("应力提取结果如下：\n")

for filename in os.listdir(odb_dir):
    if filename.endswith('.odb'):
        odb_path = os.path.join(odb_dir, filename)
        try:
            odb = openOdb(path=odb_path)

            all_mises_records = []  # 保存 (mises, step, frame, element, ip) 元组

            for step_name, step in odb.steps.items():
                for frame in step.frames:
                    time = frame.frameValue
                    stress_field = frame.fieldOutputs['S']

                    for value in stress_field.values:
                        mises = value.mises
                        record = (
                            mises,
                            step_name,
                            time,
                            getattr(value, 'elementLabel', 'N/A'),
                            value.integrationPoint
                        )
                        all_mises_records.append(record)

            if all_mises_records:
                # 排序并提取应力值
                sorted_records = sorted(all_mises_records, key=lambda x: x[0])
                mises_values = [r[0] for r in sorted_records]
                q = 99.95
                percentile_value = np.percentile(mises_values, q)

                # 找到最接近分位值的项
                closest_record = min(sorted_records, key=lambda r: abs(r[0] - percentile_value))
                max_record = max(all_mises_records, key=lambda r: r[0])

                output_line = (
                    f"[{filename}]\n"
                    f"最大Von Mises应力: {max_record[0]:.2f} MPa, "
                    f"位置: Step: {max_record[1]}, Frame: {max_record[2]}, "
                    f"Element: {max_record[3]}, Integration Point: {max_record[4]}\n"
                    f"{q}%分位应力: {percentile_value:.2f} MPa, "
                    f"最接近位置: Step: {closest_record[1]}, Frame: {closest_record[2]}, "
                    f"Element: {closest_record[3]}, Integration Point: {closest_record[4]}"
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
