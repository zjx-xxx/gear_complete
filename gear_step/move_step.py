import os
import shutil
from datetime import datetime

# 原始文件路径
original_file_1 = '../Macro/SpurGear1_cut.step'

# 获取当前时间，格式为：年月日小时分钟
timestamp = datetime.now().strftime('%Y%m%d%H%M')

# 确保目标文件夹存在
target_dir = os.path.join('..', 'output_step')
os.makedirs(target_dir, exist_ok=True)

# 构建目标文件名
base_name, ext = os.path.splitext(original_file_1)
new_filename = f"{base_name}_{timestamp}{ext}-1"

# 构建完整目标路径
target_path = os.path.join(target_dir, new_filename)

# 执行移动操作
shutil.move(original_file_1, target_path)
print(f"齿轮1文件已移动到: {target_path}")

# 原始文件路径
original_file_2 = '../Macro/SpurGear2_cut.step'

# 构建目标文件名
base_name, ext = os.path.splitext(original_file_2)
new_filename = f"{base_name}_{timestamp}{ext}-2"

# 构建完整目标路径
target_path = os.path.join(target_dir, new_filename)

# 执行移动操作
shutil.move(original_file_2, target_path)


print(f"齿轮2文件已移动到: {target_path}")
