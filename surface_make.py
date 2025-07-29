import subprocess
import os
# 这里的model_file的文件名暂时是写死了的，需要修改这个代码
def export_cgx_surface_1(component_name, model_file):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本所在目录
    cgx_path = os.path.join(base_dir,"CL34-win64", "bin","cgx216", "cgx.exe")
    script_path = os.path.join(base_dir, "export_surface_1.cgx")
    if not os.path.exists(cgx_path):
        raise FileNotFoundError(f"找不到 cgx 可执行文件: {cgx_path}")

    subprocess.run([cgx_path, "-b", "-i", script_path], check=True)

def export_cgx_surface_2(component_name, model_file):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本所在目录
    cgx_path = os.path.join(base_dir,"CL34-win64", "bin","cgx216", "cgx.exe")
    script_path = os.path.join(base_dir, "export_surface_2.cgx")
    if not os.path.exists(cgx_path):
        raise FileNotFoundError(f"找不到 cgx 可执行文件: {cgx_path}")

    subprocess.run([cgx_path, "-b", "-i", script_path], check=True)

def make_surface(component_name, model_file="assembled_gears_OUT.inp"):
    export_cgx_surface_1(component_name, model_file)
    export_cgx_surface_2(component_name, model_file)
    # export_cgx_surface_1("assembled_gears_OUT.inp", "contact_1")
    # export_cgx_surface_2("assembled_gears_OUT.inp", "contact_2")
    return
