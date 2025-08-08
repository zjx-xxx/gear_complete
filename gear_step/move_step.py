import os
import shutil
from datetime import datetime

# 获取当前时间戳
timestamp = datetime.now().strftime('%Y%m%d%H%M')

# 确保目标文件夹存在
target_dir = os.path.join('..', 'output_step')
os.makedirs(target_dir, exist_ok=True)

# 处理齿轮1
original_file_1 = '../Macro/SpurGear1_cut.step'
filename_1 = os.path.basename(original_file_1)
name_1, ext_1 = os.path.splitext(filename_1)
new_filename_1 = f"{name_1}_{timestamp}-1{ext_1}"
target_path_1 = os.path.join(target_dir, new_filename_1)
shutil.move(original_file_1, target_path_1)
print(f"齿轮1文件已移动到: {target_path_1}")

# # 处理齿轮2
# original_file_2 = '../Macro/SpurGear2_cut.step'
# filename_2 = os.path.basename(original_file_2)
# name_2, ext_2 = os.path.splitext(filename_2)
# new_filename_2 = f"{name_2}_{timestamp}-2{ext_2}"
# target_path_2 = os.path.join(target_dir, new_filename_2)
# shutil.move(original_file_2, target_path_2)
# print(f"齿轮2文件已移动到: {target_path_2}")
