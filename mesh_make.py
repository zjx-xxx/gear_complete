import gmsh
import sys
import os
import numpy as np
import math


# === 添加物理组 ===
def add_surface_group(name, tag_list):
    if not tag_list:
        print(f"⚠️ 警告: 物理组 {name} 没有找到任何面")
        return -1  # 返回无效ID

    try:
        pg = gmsh.model.addPhysicalGroup(2, tag_list)
        gmsh.model.setPhysicalName(2, pg, name)
        print(f"添加 surface 组: {name} 包含 {len(tag_list)} 个面")
        return pg
    except Exception as e:
        print(f"创建物理组 {name} 失败: {str(e)}")
        return -1

# === 用于自动给内径面进行物理分组 ===
def find_hole_surfaces(gear_volume_tag, origin_point, max_radial_distance=0.3):
    """
    精确识别内径面（孔的内表面）
    使用的逻辑是将所有中心点坐标(x,y)满足:
    x^2+y^2<=(max_radial_distance*r)^2的面分类到内径面中
    max_radial_distance可以考虑的计算方式为:
    max_radial_distance=齿轮内径/齿轮外径+0.05

    参数:
        gear_volume_tag (int): 齿轮体积标签
        origin_point (tuple): 齿轮中心点坐标 (x, y, z)
        max_radial_distance (float): 最大径向距离系数 (相对于齿轮半径)
    """
    hole_surfaces = []
    # 获取齿轮尺寸特征
    bbox = gmsh.model.getBoundingBox(3, gear_volume_tag)

    # 计算齿轮半径 (取最大尺寸的一半)
    gear_radius = max(
        (bbox[3] - bbox[0]) / 2,
        (bbox[4] - bbox[1]) / 2,
        (bbox[5] - bbox[2]) / 2
    )

    # origin = (bbox[3] + bbox[0]) / 2

    print(f"齿轮 {gear_volume_tag} 中心点: {origin_point}, 半径: {gear_radius:.2f}mm")

    # 获取所有相邻表面
    try:
        _, surfaces = gmsh.model.getAdjacencies(3, gear_volume_tag)
        print(f"齿轮 {gear_volume_tag} 共有 {len(surfaces)} 个表面")
    except Exception as e:
        print(f"获取齿轮 {gear_volume_tag} 的相邻面失败: {str(e)}")
        return hole_surfaces
    #可以通过调用log.py中的代码来打印日志信息

    for surf_tag in surfaces:
        try:
            # 获取表面中心点
            center = gmsh.model.occ.getCenterOfMass(2, surf_tag)

            # 计算到齿轮中心的径向距离（忽略Z轴差异）
            radial_vector = [
                center[0] - origin_point[0],
                center[1] - origin_point[1],
                0  # 忽略Z轴差异
            ]
            radial_distance = np.linalg.norm(radial_vector)

            # 计算法向量
            uv = gmsh.model.getParametrization(2, surf_tag, center)
            normal = gmsh.model.getNormal(surf_tag, uv)
            normal_magnitude = np.linalg.norm(normal)

            if normal_magnitude < 1e-6:
                continue

            # 归一化法向量
            normalized_normal = [n / normal_magnitude for n in normal]

            z_vector = [0,0,1]

            # 计算法向与径向向量的点积
            dot_product = sum(n * r for n, r in zip(normalized_normal, z_vector))

            # 避免数值误差导致无效值
            if abs(dot_product) > 1.0:
                dot_product = 1.0 if dot_product > 0 else -1.0

            # 内径面识别条件：
            # 1. 靠近齿轮中心（径向距离小）
            # 2. 法线方向与径向方向一致（夹角小）
            if radial_distance < max_radial_distance * gear_radius and abs(dot_product) < 0.2:
                hole_surfaces.append(surf_tag)
                print(f"  内径面候选 {surf_tag}: 径向距离={radial_distance:.2f}mm, "
                      f"法向={normal}")

        except Exception as e:
            print(f"  处理曲面 {surf_tag} 时出错: {str(e)}")
            continue

    return hole_surfaces


def find_contact_surfaces(gear_volume_tag, max_size=10.0, min_radial_distance=0.8):
    """
    基于尺寸或几何特征识别齿轮接触表面（满足任一条件）
    识别的是齿轮的完整齿面
    使用的逻辑是将所有中心点坐标(x,y)满足:
    x^2+y^2>=(min_radial_distance*r)^2的面分类到内径面中
    min_radial_distance可以考虑的计算方式为:
    min_radial_distance=齿轮内顶半径/齿轮外径-0.05


    参数:
        gear_volume_tag (int): 齿轮体积标签
        origin_point (tuple): 齿轮中心点坐标 (x, y, z)
        min_radial_distance (float): 最小径向距离系数 (相对于齿轮半径)
    """
    contact_surfaces = []

    try:
        # 获取齿轮体积的边界框和实际中心点
        bbox_gear = gmsh.model.getBoundingBox(3, gear_volume_tag)
        gear_center = [
            (bbox_gear[0] + bbox_gear[3]) / 2,
            (bbox_gear[1] + bbox_gear[4]) / 2,
            (bbox_gear[2] + bbox_gear[5]) / 2
        ]

        # 计算齿轮半径 (取最大尺寸的一半)
        gear_radius = max(
            (bbox_gear[3] - bbox_gear[0]) / 2,
            (bbox_gear[4] - bbox_gear[1]) / 2,
            (bbox_gear[5] - bbox_gear[2]) / 2
        )

        # 获取所有相邻表面
        _, surfaces = gmsh.model.getAdjacencies(3, gear_volume_tag)
    except Exception as e:
        print(f"获取齿轮 {gear_volume_tag} 信息失败: {str(e)}")
        return contact_surfaces

    # 单次遍历所有表面，应用两个条件
    for surf_tag in surfaces:
        try:
            # 获取表面边界框和尺寸
            bbox = gmsh.model.getBoundingBox(2, surf_tag)
            size_x = bbox[3] - bbox[0]
            size_y = bbox[4] - bbox[1]
            size_z = bbox[5] - bbox[2]
            surface_size = max(size_x, size_y, size_z)

            # 获取表面中心点
            center = gmsh.model.occ.getCenterOfMass(2, surf_tag)

            # 计算到齿轮中心的径向距离（XY平面）
            dx = center[0] - gear_center[0]
            dy = center[1] - gear_center[1]
            radial_distance = math.sqrt(dx * dx + dy * dy)

            # 计算法向量
            uv = gmsh.model.getParametrization(2, surf_tag, center)
            normal = gmsh.model.getNormal(surf_tag, uv)

            # 计算法向量长度并归一化
            norm = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
            normal_z = normal[2] / norm if norm > 1e-6 else 0.0

            # 两个独立条件：
            condition_size = surface_size < max_size
            condition_geometry = (
                    radial_distance > min_radial_distance * gear_radius and
                    abs(normal_z) < 0.2
            )

            # 满足任一条件即视为接触面
            if condition_size or condition_geometry:
                contact_surfaces.append(surf_tag)

                # 打印详细信息
                reason = "尺寸" if condition_size else "几何"
                if condition_size and condition_geometry:
                    reason = "尺寸和几何"

                print(f"  接触面 {surf_tag}: 原因={reason}, "
                      f"尺寸={surface_size:.2f}, "
                      f"径向距离={radial_distance:.2f}, "
                      f"法向Z={normal_z:.2f}")

        except Exception as e:
            print(f"  处理曲面 {surf_tag} 时出错: {str(e)}")
            continue

    return contact_surfaces

def make_mesh(step_path="gear_step//assembled_gear_pair.step",unv_path="assembled_gears.unv",origin_point_1=(0,0,0), origin_point_2=(73.126,0,0),):

    """

    :param step_path: 组合齿轮在项目文件根目录下的路径
    :param unv_path: 输出的unv文件在根目录下的路径
    :param origin_point_1: 齿轮1的原点坐标
    :param origin_point_2: 齿轮2的原点坐标
    :return:
    """
    # 初始化 Gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("gear_pair")

    # === 1. 载入 STEP 文件 ===
    if not os.path.exists(step_path):
        print(f"文件未找到: {step_path}")
        gmsh.finalize()
        sys.exit(1)

    try:
        gmsh.model.occ.importShapes(step_path)
        gmsh.model.occ.synchronize()
    except Exception as e:
        print(f"导入模型失败: {str(e)}")
        gmsh.finalize()
        sys.exit(1)

    # === 调试: 打印几何信息 ===
    print("=== 几何统计 ===")
    for dim in range(0, 4):
        entities = gmsh.model.getEntities(dim)
        print(f"维度 {dim} 实体数量: {len(entities)}")
        if dim == 2 and entities:
            for dim_tag, tag in entities[:3]:  # 打印前3个面的信息
                try:
                    center = gmsh.model.occ.getCenterOfMass(dim_tag, tag)
                    print(f"  面 {tag}: 中心点 {center}")
                except:
                    print(f"  面 {tag}: 无法获取中心点")

    # === 2. 添加 Volume 的物理组 ===
    volumes = gmsh.model.getEntities(dim=3)
    if not volumes:
        print("错误: 未找到任何三维体积!")
        gmsh.finalize()
        sys.exit(1)

    for i, (dim, tag) in enumerate(volumes):
        gmsh.model.addPhysicalGroup(dim, [tag], i + 1)
        gmsh.model.setPhysicalName(dim, i + 1, f"Gear{i + 1}")
    print(f"识别并添加 {len(volumes)} 个 Volume。")


    # 应用改进的表面识别
    gear1_tag = volumes[0][1]  # 第一个齿轮
    gear2_tag = volumes[1][1]  # 第二个齿轮

    print("识别孔表面...")
    gear1_hole = find_hole_surfaces(gear1_tag, origin_point_1)
    print(f"齿轮1孔表面: {len(gear1_hole)}个面")
    gear2_hole = find_hole_surfaces(gear2_tag, origin_point_2)
    print(f"齿轮2孔表面: {len(gear2_hole)}个面")

    print("识别接触表面...")
    gear1_contact = find_contact_surfaces(gear1_tag, max_size=15.0)
    print(f"齿轮1接触面: {len(gear1_contact)}个面")
    gear2_contact = find_contact_surfaces(gear2_tag, max_size=15.0)
    print(f"齿轮2接触面: {len(gear2_contact)}个面")


    #如果获取失败，那么需要在日志里给出报错信息
    # # 后备方案：如果自动识别失败，使用硬编码标签
    # if not gear1_hole:
    #     print("⚠️ 警告: 齿轮1孔表面未自动识别，使用后备方案")
    #     gear1_hole = [1]  # 替换为实际标签
    #
    # if not gear2_hole:
    #     print("⚠️ 警告: 齿轮2孔表面未自动识别，使用后备方案")
    #     gear2_hole = [1942]  # 替换为实际标签
    #
    # if not gear1_contact:
    #     print("⚠️ 警告: 齿轮1接触面未自动识别，使用后备方案")
    #     gear1_contact = list(range(4, 1942))  # 替换为实际范围
    #
    # if not gear2_contact:
    #     print("⚠️ 警告: 齿轮2接触面未自动识别，使用后备方案")
    #     gear2_contact = list(range(1944, 1963)) + list(range(1964, 1985))  # 替换为实际范围




    hole1_pg = add_surface_group('hole_gear_1', gear1_hole)
    hole2_pg = add_surface_group('hole_gear_2', gear2_hole)
    contact1_pg = add_surface_group('contact_1', gear1_contact)
    contact2_pg = add_surface_group('contact_2', gear2_contact)

    gmsh.model.occ.synchronize()

    # === 4. 删除未分组的 surface 实体 ===
    all_surface_tags = [tag for dim, tag in gmsh.model.getEntities(2)]
    physical_surface_tags = []

    # 修复: 正确处理空物理组
    for dim, pg in gmsh.model.getPhysicalGroups(dim=2):
        try:
            tags = gmsh.model.getEntitiesForPhysicalGroup(dim, pg)
            if tags:  # 只添加非空列表
                physical_surface_tags += list(tags)
        except Exception as e:
            print(f"获取物理组 {pg} 的实体失败: {str(e)}")

    # 找出未分配的标签
    surfaces_to_delete_tags = list(set(all_surface_tags) - set(physical_surface_tags))

    # 转换为实体格式
    surfaces_to_delete = [(2, tag) for tag in surfaces_to_delete_tags]

    if surfaces_to_delete:
        print(f"删除 {len(surfaces_to_delete)} 个未分组的面")
        try:
            gmsh.model.occ.remove(surfaces_to_delete, recursive=True)
        except Exception as e:
            print(f"删除面时出错: {str(e)}")
    else:
        print("没有未分组的面需要删除")

    gmsh.model.occ.synchronize()

    # === 5. 设置网格尺寸与细化控制 ===
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.5)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 5.0)

    # 添加曲率自适应
    gmsh.model.mesh.field.add("Curvature", 1)
    gmsh.model.mesh.field.add("Threshold", 2)
    gmsh.model.mesh.field.setNumber(2, "InField", 1)
    gmsh.model.mesh.field.setNumber(2, "SizeMin", 0.3)
    gmsh.model.mesh.field.setNumber(2, "SizeMax", 5.0)
    gmsh.model.mesh.field.setNumber(2, "DistMin", 0.05)
    gmsh.model.mesh.field.setNumber(2, "DistMax", 1.0)
    gmsh.model.mesh.field.setAsBackgroundMesh(2)

    # 添加网格优化
    gmsh.option.setNumber("Mesh.Optimize", 1)
    gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)

    # === 6. 网格生成 ===
    print("开始生成三维网格...")
    try:
        gmsh.model.mesh.generate(3)
        print("网格完成。")
    except Exception as e:
        print(f"网格生成失败: {str(e)}")
        gmsh.finalize()
        sys.exit(1)

    # 检查网格质量
    try:
        element_types, element_tags, node_tags = gmsh.model.mesh.getElements(3)
        if element_tags:
            print(f"生成 {len(element_tags[0])} 个体单元")
        else:
            print("警告: 未生成任何体单元")
    except:
        print("无法获取网格元素信息")

    gmsh.option.setNumber("Mesh.SaveAll", 0)

    # === 7. 导出文件 ===
    # inp_file = "gear_step//assembled_gears_curvature.inp"
    # try:
    #     gmsh.write(inp_file)
    #     print(f"导出完成: {inp_file}")
    # except Exception as e:
    #     print(f"导出INP文件失败: {str(e)}")

    gmsh.option.setNumber("Mesh.SaveAll", 1)
    gmsh.option.setNumber("Mesh.SaveGroupsOfNodes", 1)
    gmsh.write(unv_path)

    # # === 9. 打开 Gmsh GUI 查看 ===
    # print("在GUI中查看网格...")
    # try:
    #     gmsh.fltk.run()
    # except:
    #     print("无法打开GUI")

    gmsh.finalize()
    return