import cadquery as cq
import math
def assemble_gear(modulus=3.75,z1=19,z2=20,center_distance=73.125,
                   gear1_file_name="./Macro/SpurGear1_cut.step",
                   gear2_file_name="./Macro/SpurGear2_cut.step",
                   gear_assembled_file_name="./gear_step/assembled_gear_pair.step"):
    """
    :param modulus:齿轮模数
    :param z1:齿轮1齿数
    :param z2:齿轮2齿数
    :param center_distance:两齿轮中心距
    :param gear1_file_name:齿轮1在项目根目录下的路径
    :param gear2_file_name:齿轮2在项目根目录下的路径
    :param gear_assembled_file_name:默认的生成合并齿轮组路径
    :return:是否成功导出
    """
    # === 参数 ===
    gear2_align_angle = 360 / (2 * z2)  # 齿槽对齐

    # === 加载 STEP 文件 ===
    gear1 = cq.importers.importStep(gear1_file_name)
    gear2 = cq.importers.importStep(gear2_file_name)

    # === 移动和旋转 gear2 使其正确啮合 ===
    gear2 = gear2.rotate((0, 0, 0), (0, 0, 1), -1 * gear2_align_angle)
    gear2 = gear2.translate((center_distance + 0.001, 0, 0))

    # === 合并两个齿轮模型 ===
    assembly = gear1.union(gear2)

    # === 导出为组合的 STEP 文件 ===
    cq.exporters.export(assembly, gear_assembled_file_name)

    # print("导出成功：assembled_gear_pair.step")
    return f"导出成功：{gear_assembled_file_name}"