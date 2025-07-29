import os
import shutil
from datetime import datetime

# 原始文件路径
original_file = 'assembled_gear_pair.step'

# 获取当前时间，格式为：年月日小时分钟
timestamp = datetime.now().strftime('%Y%m%d%H%M')

# 确保目标文件夹存在
target_dir = os.path.join('..', 'output_step')
os.makedirs(target_dir, exist_ok=True)

# 构建目标文件名
base_name, ext = os.path.splitext(original_file)
new_filename = f"{base_name}_{timestamp}{ext}"

# 构建完整目标路径
target_path = os.path.join(target_dir, new_filename)

# 执行移动操作
shutil.move(original_file, target_path)

print(f"文件已移动到: {target_path}")
