# -*- coding: utf-8 -*-
"""
多节线批处理版本（第5条已给定）：
- 以 REF_COORD(i) 的 (x,y) 为圆心，半径 R_REGION 的圆盘内元素质心作为研究范围
- 抽取这些元素在所有帧上的 Von Mises 应力
- 按用户自定义分位最小/最大/步长绘制分位曲线（Y 轴为对数）
- 程序仅自动调整绘图精细度（DPI/线宽/点大小/刻度密度），不改你的步长
"""

from odbAccess import openOdb
import numpy as np
import os, math, glob

# ========= 必填配置 =========
# 若需要限定目录，可把 "." 改为具体路径
ODB_DIR = "."                                 # <--- 遍历该目录下所有 .odb
instance_name = "ASSEMBLED_GEAR_PAIR-1-1"    # <--- 改成你的实例名

# 仅用于日志展示
CENTER_X, CENTER_Y = 0.0, 0.0

# ✅ 多条节线的参考坐标（None 的先占位，填上(x,y,z)就会参与运算）
#    第 5 条已填入你给的坐标
REF_COORDS = {
    1: (32.136979,13.782776,8.656675),
    2: (33.052997,8.945748,1.813109),
    3: (34.635532,2.484884,3.153081),
    4: (34.635532,-2.484884,3.153081),
    5: (33.21232719421387, -8.887279987335205, 7.518895483016967),
    6: (31.757954,-13.408759,0)
}

# 选区半径（单位同模型）
R_REGION = 1.0

# ✅ 分位区间与步长
P_MIN, P_MAX, P_STEP = 80.0, 100.0, 0.02

# 曲线标注的一个分位点（可选）
percentile_q = 95.0

# 输出目录
PLOT_DIR = "./plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ========= Matplotlib（无显示 + 中文） =========
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


# ========= 基础工具函数 =========
def build_centroids(instance):
    """返回 [(label, centroid_xyz)]"""
    out = []
    get_node = instance.getNodeFromLabel
    for e in instance.elements:
        try:
            pts = [get_node(n).coordinates for n in e.connectivity]
            c = np.mean(pts, axis=0)
            out.append((e.label, c))
        except:
            continue
    return out


def select_labels_in_xy_disk(centroids, cx, cy, r_region):
    """按 XY 平面圆盘筛选：||(x-cx, y-cy)|| <= r_region"""
    r2 = float(r_region) ** 2
    labels = []
    for lbl, c in centroids:
        dx = float(c[0]) - cx
        dy = float(c[1]) - cy
        if dx*dx + dy*dy <= r2:
            labels.append(lbl)
    return sorted(set(labels))


def extract_stresses(odb, instance_name, element_labels):
    """返回应力列表（所有选中元素、所有帧汇总的 Von Mises）"""
    if not element_labels:
        return []
    labels_set = set(element_labels)
    vals = []
    for step_name, step in odb.steps.items():
        for frame in step.frames:
            if 'S' not in frame.fieldOutputs:
                continue
            S = frame.fieldOutputs['S']
            for v in S.values:
                if v.instance.name == instance_name and v.elementLabel in labels_set:
                    vals.append(float(v.mises))
    return vals


# === 仅自动“画图精细度”，不修改你的步长 ===
def _auto_style_from_span(span, n_points):
    """根据分位范围跨度与点数自动调画图精细度（DPI/线宽/点大小/刻度密度）"""
    density = n_points / max(1e-9, span) if span > 0 else n_points
    dpi, lw, ms, xtick = 200, 1.2, 2.0, max(1.0, round(span / 10.0))
    if density >= 80:
        dpi, lw, ms, xtick = 400, 2.2, 3.5, max(0.2, span/12)
    elif density >= 40:
        dpi, lw, ms, xtick = 350, 2.0, 3.2, max(0.5, span/10)
    elif density >= 15:
        dpi, lw, ms, xtick = 300, 1.8, 3.0, max(1.0, span/8)
    elif density >= 5:
        dpi, lw, ms, xtick = 260, 1.5, 2.5, max(2.0, span/6)
    else:
        dpi, lw, ms, xtick = 220, 1.3, 2.0, max(5.0, span/5)
    return {"dpi": dpi, "line_width": lw, "marker_size": ms, "xtick_major": xtick}


def _decimals_for_values(arr):
    """根据波动大小自适应小数位（1~3 位），用于标注文本"""
    arr = np.asarray(arr, dtype=float)
    if arr.size < 2:
        return 2
    v = np.nanmax(arr) - np.nanmin(arr)
    if v < 0.5:
        return 3
    elif v < 5:
        return 2
    else:
        return 1


def plot_percentile_curve_auto(stresses, out_png, title, percentile_q=95.0,
                               p_min=80.0, p_max=100.0, p_step=0.02,
                               csv_path=None):
    """按用户给定的分位范围与步长取点，自动调图像精细度；Y 轴对数；可输出CSV"""
    stresses = np.asarray(stresses, dtype=float)
    stresses = stresses[np.isfinite(stresses)]
    if stresses.size == 0:
        raise ValueError("stresses 为空或全是非有限数，无法绘图")

    # 限制到 [0,100]
    p_lo = float(max(0.0, min(100.0, p_min)))
    p_hi = float(max(0.0, min(100.0, p_max)))
    if p_hi <= p_lo:
        p_lo, p_hi = 0.0, 100.0
    span = p_hi - p_lo

    # 用 linspace 精确包含右端点
    n = max(1, int(round(span / float(p_step))))
    percentiles = np.linspace(p_lo, p_hi, n + 1, endpoint=True)
    percentiles = np.clip(percentiles, 0.0, 100.0)

    ys = [np.percentile(stresses, float(p)) for p in percentiles]

    # === 保存为 CSV ===
    if csv_path is not None:
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Percentile (%)", "Von Mises Stress (MPa)"])
            for p, val in zip(percentiles, ys):
                writer.writerow([f"{p:.6f}", f"{val:.6f}"])

    vmax = float(np.max(stresses))
    p_val = float(np.percentile(stresses, float(percentile_q)))
    style = _auto_style_from_span(span, len(percentiles))
    d = _decimals_for_values(ys)

    plt.figure(figsize=(8, 5), dpi=style["dpi"])
    plt.plot(percentiles, ys, marker='o',
             markersize=style["marker_size"], linewidth=style["line_width"],
             label='应力分位曲线')

    # 标注
    if p_lo <= 100.0 <= p_hi:
        plt.scatter(100, vmax, label=u'最大值 {:.{d}f} MPa'.format(vmax, d=d))
        plt.text(100, vmax, ('{:.%df}' % d).format(vmax), fontsize=9)
    if p_lo <= percentile_q <= p_hi:
        plt.scatter(percentile_q, p_val,
                    label=u'{:.2f}% 分位 {:.{d}f} MPa'.format(percentile_q, p_val, d=d))
        plt.text(percentile_q, p_val, ('{:.%df}' % d).format(p_val), fontsize=9)

    plt.xlabel('分位数 (%)')
    plt.ylabel('Von Mises 应力 (MPa)')
    plt.title(title)
    plt.grid(True, linewidth=0.5, alpha=0.6)
    plt.xlim(p_lo, p_hi)
    plt.yscale("log")
    xtick_major = style["xtick_major"]
    ticks = np.arange(p_lo, p_hi + 1e-9, xtick_major)
    ticks = np.clip(ticks, 0.0, 100.0)
    plt.xticks(ticks)

    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=style["dpi"])
    plt.close()


# ========= 业务包装函数 =========
def analyze_pitchline(odb, instance_name, centroids, ref_coord, r_region,
                      p_min, p_max, p_step, percentile_q, plot_dir, tag="L",
                      odb_path_for_naming="unknown.odb"):
    """
    对单条节线执行：圆盘选元 -> 提取所有帧 Von Mises -> 绘图+CSV
    返回：输出图片路径 或 None
    """
    rx, ry, rz = ref_coord
    print(f"[{tag}] 邻域中心: ({rx:.6f}, {ry:.6f}), 半径: {r_region}")
    labels = select_labels_in_xy_disk(centroids, rx, ry, r_region)
    print(f"[{tag}] 选中的元素数: {len(labels)}")
    if not labels:
        print(f"[{tag}] ❌ 未匹配到元素；请增大 R_REGION 或检查坐标。")
        return None

    stresses = extract_stresses(odb, instance_name, labels)
    if not stresses:
        print(f"[{tag}] ❌ 选中元素无应力数据（S 场缺失或过滤条件不匹配）。")
        return None

    base = os.path.splitext(os.path.basename(odb_path_for_naming))[0]
    fn_base = f"{base}_{tag}_xyDisk_{r_region:.2f}_p{p_min:.2f}-{p_max:.2f}_step{p_step}"
    out_png = os.path.join(plot_dir, fn_base + ".png")
    out_csv = os.path.join(plot_dir, fn_base + ".csv")

    plot_percentile_curve_auto(
        stresses, out_png,
        title=f"{base} - 邻域分位曲线 ({tag}, r={r_region})",
        percentile_q=percentile_q,
        p_min=p_min, p_max=p_max, p_step=p_step,
        csv_path=out_csv
    )
    print(f"[{tag}] ✅ 分位曲线图已保存: {out_png}")
    print(f"[{tag}] 📄 分位数据CSV已保存: {out_csv}")
    return out_png


def analyze_multiple_pitchlines(odb_path, instance_name, ref_coords_map,
                                r_region=1.0,
                                p_min=80.0, p_max=100.0, p_step=0.02,
                                percentile_q=95.0,
                                plot_dir="./plots"):
    """
    批量处理多条节线（ref_coords_map: {index:int -> (x,y,z) or None}）
    跳过为 None 的条目；其余逐条处理。
    """
    print(f"圆心(展示用): ({CENTER_X:.6f}, {CENTER_Y:.6f})")
    print(f"分位设置: [{p_min:.4f}, {p_max:.4f}]，步长: {p_step}")
    print(f"输出目录: {os.path.abspath(plot_dir)}\n")

    odb = None
    outputs = {}
    try:
        odb = openOdb(path=odb_path, readOnly=True)
        if instance_name not in odb.rootAssembly.instances:
            raise KeyError(f"实例 {instance_name} 在 {os.path.basename(odb_path)} 中不存在")
        inst = odb.rootAssembly.instances[instance_name]

        centroids = build_centroids(inst)
        print(f"实例共有元素数: {len(centroids)}\n")

        for idx in sorted(ref_coords_map.keys()):
            rc = ref_coords_map[idx]
            tag = f"L{idx}"
            if rc is None:
                print(f"[{tag}] 跳过：未提供 REF_COORD。")
                continue
            try:
                out_png = analyze_pitchline(
                    odb, instance_name, centroids, rc, r_region,
                    p_min, p_max, p_step, percentile_q, plot_dir, tag=tag,
                    odb_path_for_naming=odb_path
                )
                outputs[tag] = out_png
            except Exception as e:
                print(f"[{tag}] 错误: {e}")
                outputs[tag] = None

        return outputs

    finally:
        if odb is not None:
            odb.close()


# ========= 脚本入口：遍历目录下所有 .odb =========
if __name__ == "__main__":
    odb_files = sorted(glob.glob(os.path.join(ODB_DIR, "*.odb")))
    if not odb_files:
        print(f"⚠️ 在目录 {os.path.abspath(ODB_DIR)} 下未找到任何 .odb 文件。")
    else:
        print(f"🔎 在目录 {os.path.abspath(ODB_DIR)} 下找到 {len(odb_files)} 个 .odb 文件。\n")

    all_results = {}
    for odb_path in odb_files:
        print("=" * 80)
        print(f"▶ 处理 ODB: {os.path.basename(odb_path)}")
        try:
            results = analyze_multiple_pitchlines(
                odb_path=odb_path,
                instance_name=instance_name,
                ref_coords_map=REF_COORDS,
                r_region=R_REGION,
                p_min=P_MIN, p_max=P_MAX, p_step=P_STEP,
                percentile_q=percentile_q,
                plot_dir=PLOT_DIR
            )
            all_results[os.path.basename(odb_path)] = results
        except Exception as e:
            print(f"❌ 处理 {os.path.basename(odb_path)} 失败：{e}")
        print("")

    print("\n=== 全部 ODB 生成结果一览 ===")
    for odb_name, res in all_results.items():
        print(f"\n[{odb_name}]")
        for tag, path in (res or {}).items():
            print(f"  {tag}: {path}")
