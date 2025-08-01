import os
import numpy as np
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
from OCC.Core.TopoDS import topods, TopoDS_Compound
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.BRep import BRep_Tool, BRep_Builder
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Mat, gp_Trsf, gp_GTrsf, gp_Quaternion
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform

def read_step_shape(filepath):
    reader = STEPControl_Reader()
    status = reader.ReadFile(filepath)
    if status != 1:
        raise RuntimeError(f"STEP文件读取失败: {filepath}")
    reader.TransferRoot()
    return reader.Shape()

def write_step_shape(shape, filepath):
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    writer.Write(filepath)
    print(f"✅ 已导出 STEP: {filepath}")

def scale_shape(shape, sx, sy, sz):
    mat = gp_Mat(sx, 0, 0, 0, sy, 0, 0, 0, sz)
    gtrsf = gp_GTrsf()
    gtrsf.SetVectorialPart(mat)
    return BRepBuilderAPI_GTransform(shape, gtrsf, True).Shape()

def rotate_shape_to_dir(shape, target_dir):
    from_dir = gp_Dir(0, 1, 0)
    q = gp_Quaternion(gp_Vec(from_dir), gp_Vec(target_dir))
    trsf = gp_Trsf()
    trsf.SetRotation(q)
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

def translate_shape(shape, target_center):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(gp_Pnt(0, 0, 0), target_center))
    return BRepBuilderAPI_Transform(shape, trsf).Shape()

def generate_pit_centers(num_centers=3, u_pitch=0.2775, u_eps=0.0125):
    centers = []
    min_v_dist = 0.15  # 控制 v 方向最小间距（范围 0.232 到 0.768 大约有 0.5 可用）

    v_min, v_max = 0.232, 0.768
    max_attempts = 1000

    print("中心点分布：")

    for i in range(num_centers):
        attempt = 0
        while attempt < max_attempts:
            u = np.random.uniform(u_pitch - u_eps, u_pitch + u_eps)
            v = np.random.uniform(v_min, v_max)

            # 与已有中心点保持 v 方向分散
            if all(abs(v - prev_v) > min_v_dist for _, prev_v in centers):
                centers.append((u, v))
                print(f"第{i+1}个中心点的v坐标是{v:.4f}")
                break
            attempt += 1
        else:
            print(f"第{i+1}个中心点生成失败（尝试超过{max_attempts}次），放弃该点")

    return centers

def generate_pit_cluster(center_uv, level=3, std_u=0.05, std_v=0.3):
    u0, v0 = center_uv
    pits = []
    num_list = [16, 7, 3]
    num = num_list[level-1]
    for i in range(1, level+1):
        # num = int((12 - level * 3.6) * 2)
        # ru = std_u * (layer + 1)
        # rv = std_v * (layer + 1)
        # # 直径可以动态变化 16 24
        # # 直径缩放比例0.01；0.007；0.004
        # # （0.16, 0.12） (0.112, 0.084) (0.0784,0.0588)
        # radius = 0.01 * (1.0 - 0.3 * layer)
        # u_samples = np.random.normal(u0, ru, num)
        # v_samples = np.random.normal(v0, rv, num)
        # for u, v in zip(u_samples, v_samples):
        #     if 0 < u < 0.5 and 0.2 < v < 0.8:
        #         pits.append((u, v, radius))
        ru = std_u * (level + 2 - i) * std_u
        rv = std_v * (level + 2 - i) * std_v
        radius = 0.02 * i
        u_samples = np.random.normal(u0, ru, num)
        v_samples = np.random.normal(v0, rv, num)
        for u, v in zip(u_samples, v_samples):
            if 0 < u < 0.5 and 0.2 < v < 0.8:
                pits.append((u, v, radius))
    return pits

def generate_all_pits_from_pitch(num_centers=3, level=3):
    centers = generate_pit_centers(num_centers)
    pit_uv_list = []
    scale_xyz_list = []
    for center in centers:
        cluster = generate_pit_cluster(center, level)
        for u, v, r in cluster:
            pit_uv_list.append((u, v))
            scale_xyz_list.append((np.random.uniform(1, level) * r, 0.6 * r, np.random.uniform(1, (level * 1.25)) * r)) # (宽, 深, 长)
    return pit_uv_list, scale_xyz_list

def extract_pit_info_from_faces(shape, target_face_ids, pit_uv_list, scale_xyz_list):
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    face_map = {}
    face_idx = -1
    while exp.More():
        face_idx += 1
        face = topods.Face(exp.Current())
        if face_idx in target_face_ids:
            face_map[face_idx] = face
        exp.Next()

    grouped_info = {fid: [] for fid in face_map}

    for face_id, face in face_map.items():
        surf = BRep_Tool.Surface(face)
        adaptor = GeomAdaptor_Surface(surf)
        umin, umax = adaptor.FirstUParameter(), adaptor.LastUParameter()
        vmin, vmax = adaptor.FirstVParameter(), adaptor.LastVParameter()

        for i, (u_norm, v_norm) in enumerate(pit_uv_list):
            u1 = umin + u_norm * (umax - umin)
            v1 = vmin + v_norm * (vmax - vmin)
            u2 = umin + (1 - u_norm) * (umax - umin)
            v2 = v1
            scale_xyz = scale_xyz_list[i]

            pnt1 = gp_Pnt()
            surf.D0(u1, v1, pnt1)
            props1 = GeomLProp_SLProps(surf, u1, v1, 1, 1e-6)
            if props1.IsNormalDefined():
                normal1 = props1.Normal()
                grouped_info[face_id].append((pnt1, normal1, scale_xyz))

            pnt2 = gp_Pnt()
            surf.D0(u2, v2, pnt2)
            props2 = GeomLProp_SLProps(surf, u2, v2, 1, 1e-6)
            if props2.IsNormalDefined():
                normal2 = props2.Normal()
                mirrored_normal = gp_Dir(-normal2.X(), -normal2.Y(), -normal2.Z())
                grouped_info[face_id].append((pnt2, mirrored_normal, scale_xyz))

    return grouped_info

def build_ellipsoid_compound(pit_info_list, ellipsoid_template_path):
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for pnt, normal, scale_xyz in pit_info_list:
        ellipsoid = read_step_shape(ellipsoid_template_path)
        ellipsoid = scale_shape(ellipsoid, *scale_xyz)
        ellipsoid = rotate_shape_to_dir(ellipsoid, normal)
        ellipsoid = translate_shape(ellipsoid, pnt)
        builder.Add(compound, ellipsoid)
    return compound

def cut_ellipsoids_on_faces_per_face(step_path, ellipsoid_template_path, grouped_info, output_path):
    shape = read_step_shape(step_path)
    result = shape
    for face_id, pit_info_list in grouped_info.items():
        print(f"🔧 正在处理 Face ID = {face_id}, 坑数量 = {len(pit_info_list)}")
        compound = build_ellipsoid_compound(pit_info_list, ellipsoid_template_path)
        result = BRepAlgoAPI_Cut(result, compound).Shape()
    write_step_shape(result, output_path)

def fuse_ellipsoids(pit_info_list, ellipsoid_template_path):
    """将多个椭球按顺序 fuse 成一个 shape"""
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse

    fused_shape = None
    for idx, (pnt, normal, scale_xyz) in enumerate(pit_info_list):
        ellipsoid = read_step_shape(ellipsoid_template_path)
        ellipsoid = scale_shape(ellipsoid, *scale_xyz)
        ellipsoid = rotate_shape_to_dir(ellipsoid, normal)
        ellipsoid = translate_shape(ellipsoid, pnt)
        if fused_shape is None:
            fused_shape = ellipsoid
        else:
            fused_shape = BRepAlgoAPI_Fuse(fused_shape, ellipsoid).Shape()
    return fused_shape


def cut_ellipsoids_on_faces_per_face_fused(step_path, ellipsoid_template_path, grouped_info, output_path):
    """每个面内的椭球先 fuse 成一个 shape，再 cut 原工件"""
    shape = read_step_shape(step_path)
    result = shape
    for face_id, pit_info_list in grouped_info.items():
        print(f"🛠️ 正在处理 Face ID = {face_id}, 椭球数量 = {len(pit_info_list)}")
        fused_ellipsoids = fuse_ellipsoids(pit_info_list, ellipsoid_template_path)
        result = BRepAlgoAPI_Cut(result, fused_ellipsoids).Shape()
    write_step_shape(result, output_path)

def main():
    step_path = "./SpurGear1.STEP"
    output_path = "./SpurGear1_cut.step"
    ellipsoid_template_path = "./tuoqiu.STEP"
    target_face_ids = {22, 23, 26}
    pit_uv_list, scale_xyz_list = generate_all_pits_from_pitch(num_centers=3, level=1)
    shape = read_step_shape(step_path)
    grouped_info = extract_pit_info_from_faces(shape, target_face_ids, pit_uv_list, scale_xyz_list)
    cut_ellipsoids_on_faces_per_face_fused(step_path, ellipsoid_template_path, grouped_info, output_path)


if __name__ == '__main__':
    main()
