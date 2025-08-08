import cadquery as cq
import math

# === 参数 ===
modulus = 3.75
z1, z2 = 19, 20
face_width1 = 36
face_width2 = 15
center_distance = modulus * (z1 + z2) / 2
gear2_align_angle = 360 / (2 * z2)  # 齿槽对齐

# === 加载 STEP 文件 ===
gear1 = cq.importers.importStep("./Macro/SpurGear1_cut.step")
# gear2 = cq.importers.importStep("./Macro/SpurGear2_cut.step")
gear2 = cq.importers.importStep("./Macro/SpurGear2.step")

# === 移动和旋转 gear2 使其正确啮合 ===
gear2 = gear2.rotate((0, 0, 0), (0, 0, 1), -1 * gear2_align_angle)
gear2 = gear2.translate((center_distance + 0.001, 0, 0))

# === 合并两个齿轮模型 ===
assembly = gear1.union(gear2)

# === 导出为组合的 STEP 文件 ===
cq.exporters.export(assembly, "./gear_step/assembled_gear_pair.step")

print("extract successfully:assembled_gear_pair.step")