import os
import random
import math
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.TopoDS import topods, TopoDS_Compound
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.BRep import BRep_Tool, BRep_Builder
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_BSplineSurface, GeomAbs_BezierSurface
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.gp import gp_Pnt, gp_Vec


def generate_distinct_uv_points(n: int, min_distance: float = 0.05):
    uv_list = []
    attempts = 0
    max_attempts = n * 50
    while len(uv_list) < n and attempts < max_attempts:
        u = round(random.uniform(0.1, 0.5), 2)
        v = round(random.uniform(0.2, 0.8), 2)
        candidate = (u, v)
        if all(math.hypot(u - u0, v - v0) >= min_distance for (u0, v0) in uv_list):
            uv_list.append(candidate)
        attempts += 1
    if len(uv_list) < n:
        raise RuntimeError(f"❌ 仅生成了 {len(uv_list)} 个合格点，可能 min_distance 设置过大")
    return uv_list


def create_cut_spheres_on_face(face, pit_uv_list, sphere_radius_list, offset_distance_list):
    surf = BRep_Tool.Surface(face)
    adaptor = GeomAdaptor_Surface(surf)
    u_min, u_max = adaptor.FirstUParameter(), adaptor.LastUParameter()
    v_min, v_max = adaptor.FirstVParameter(), adaptor.LastVParameter()

    spheres = []
    for i, (u_norm, v_norm) in enumerate(pit_uv_list):
        u = u_min + u_norm * (u_max - u_min)
        v = v_min + v_norm * (v_max - v_min)
        pnt = gp_Pnt()
        surf.D0(u, v, pnt)
        props = GeomLProp_SLProps(surf, u, v, 1, 1e-6)
        if not props.IsNormalDefined():
            print(f"⚠️ 凹坑 {i} 法向未定义，跳过")
            continue
        normal = gp_Vec(props.Normal())
        center = pnt.Translated(normal.Scaled(offset_distance_list[i]))
        sphere = BRepPrimAPI_MakeSphere(center, sphere_radius_list[i]).Shape()
        spheres.append(sphere)

    return spheres


def group_faces_into_compound(shape, target_face_ids):
    """将指定面ID的面（及其碎片）合并为 compound"""
    face_idx = 0
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    builder = BRep_Builder()

    compound_dict = {}
    while exp.More():
        face = topods.Face(exp.Current())

        # 模拟匹配面：用原始面 ID 做索引（实际项目可用几何属性匹配）
        for face_id in target_face_ids:
            if face_id not in compound_dict:
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)
                compound_dict[face_id] = compound
            builder.Add(compound_dict[face_id], face)
        exp.Next()
        face_idx += 1

    return list(compound_dict.values())


def write_compounds_to_step(compounds, output_path):
    writer = STEPControl_Writer()
    for comp in compounds:
        writer.Transfer(comp, STEPControl_AsIs)
    writer.Write(output_path)
    print(f"✅ 已写入包含多个 Compound 的 STEP 文件：{output_path}")


def main():
    STEP_PATH = r"D:\Code\pyansys\nojian\SpurGear2.STEP"
    CUT_OUTPUT_PATH = r"D:\Code\pyansys\nojian\SpurGear2_cut_new.step"
    COMPOUND_OUTPUT_PATH = r"D:\Code\pyansys\nojian\SpurGear2_compound_faces_new.step"

    reader = STEPControl_Reader()
    if reader.ReadFile(STEP_PATH) != 1:
        raise RuntimeError("❌ STEP 文件读取失败")
    reader.TransferRoot()
    shape = reader.Shape()

    target_face_ids = {37, 38}
    pit_uv_list_left = generate_distinct_uv_points(50, min_distance=0.05)
    pit_uv_list = pit_uv_list_left + [(round(1 - u, 2), v) for u, v in pit_uv_list_left]
    sphere_radius_list = [0.5] * len(pit_uv_list)
    offset_distance_list = [0.4] * len(pit_uv_list)

    all_spheres = []
    face_idx = 0
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = topods.Face(exp.Current())
        adaptor = GeomAdaptor_Surface(BRep_Tool.Surface(face))
        surf_type = adaptor.GetType()

        if face_idx in target_face_ids and surf_type in (GeomAbs_BSplineSurface, GeomAbs_BezierSurface):
            print(f"🟢 处理目标面 ID={face_idx} 的 NURBS 面...")
            spheres = create_cut_spheres_on_face(face, pit_uv_list, sphere_radius_list, offset_distance_list)
            all_spheres.extend(spheres)

        face_idx += 1
        exp.Next()

    if not all_spheres:
        raise RuntimeError("❌ 未生成任何球体")

    fused_spheres = all_spheres[0]
    for s in all_spheres[1:]:
        fused_spheres = BRepAlgoAPI_Fuse(fused_spheres, s).Shape()

    print("⏳ 正在执行布尔差运算...")
    cut_result = BRepAlgoAPI_Cut(shape, fused_spheres).Shape()

    # 保存布尔减后的中间结果
    writer = STEPControl_Writer()
    writer.Transfer(cut_result, STEPControl_AsIs)
    writer.Write(CUT_OUTPUT_PATH)
    print(f"✅ 中间布尔结果保存：{CUT_OUTPUT_PATH}")

    # 合并面块
    compounds = group_faces_into_compound(cut_result, target_face_ids)
    write_compounds_to_step(compounds, COMPOUND_OUTPUT_PATH)


if __name__ == "__main__":
    main()
