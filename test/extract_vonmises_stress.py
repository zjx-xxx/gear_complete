# -*- coding: utf-8 -*-
from odbAccess import openOdb
import numpy as np

def get_element_centroid(odb_path, instance_name, element_label):
    """
    返回元素质心坐标 (x, y, z)；若未找到返回 None
    质心=所有节点坐标的平均
    """
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        inst = odb.rootAssembly.instances[instance_name]
        try:
            elem = inst.getElementFromLabel(element_label)
        except Exception:
            return None  # 没找到该元素
        coords = [inst.getNodeFromLabel(nid).coordinates for nid in elem.connectivity]
        centroid = np.mean(np.array(coords, dtype=float), axis=0)
        return tuple(float(v) for v in centroid)
    finally:
        odb.close()

def get_element_nodes_coords(odb_path, instance_name, element_label):
    """
    返回该元素所有节点的 {node_label: (x,y,z)} 字典；未找到返回 {}
    """
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        inst = odb.rootAssembly.instances[instance_name]
        try:
            elem = inst.getElementFromLabel(element_label)
        except Exception:
            return {}
        out = {}
        for nid in elem.connectivity:
            nd = inst.getNodeFromLabel(nid)
            out[nid] = tuple(float(v) for v in nd.coordinates)
        return out
    finally:
        odb.close()

def get_node_coords(odb_path, instance_name, node_label):
    """
    返回指定节点坐标 (x, y, z)；未找到返回 None
    """
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        inst = odb.rootAssembly.instances[instance_name]
        try:
            nd = inst.getNodeFromLabel(node_label)
        except Exception:
            return None
        return tuple(float(v) for v in nd.coordinates)
    finally:
        odb.close()


# ===== 用法示例 =====
if __name__ == "__main__":
    odb_path = "ZZ35_20250804_1511.odb"
    inst_name = "ASSEMBLED_GEAR_PAIR-1-1"

    lbl = 87216  # 你的元素label
    cent = get_element_centroid(odb_path, inst_name, lbl)
    print("元素质心：", cent)

    nodes = get_element_nodes_coords(odb_path, inst_name, lbl)
    print("元素节点坐标：", nodes)

    nd_lbl = next(iter(nodes)) if nodes else None
    if nd_lbl:
        nd_xyz = get_node_coords(odb_path, inst_name, nd_lbl)
        print(f"节点{nd_lbl}坐标：", nd_xyz)
