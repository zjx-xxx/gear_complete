from unv2xc import *

inp_to_med_C3D10 = [1,3,5,10,2,4,6,7,8,9]
inp_to_med_C3D20 = [1,3,5,7,13,15,17,19,2,4,6,8,14,16,18,20,9,10,11,12]
inp_to_med_S6 = [1,3,5,2,4,6]
inp_to_med_S8 = [1,3,5,7,2,4,6,8]
inp_to_med_C3D15 = [1,3,5,10,12,14,2,4,6,11,13,15,7,8,9]

def convert_unv_to_inp(unvfile, out_inp_path, reduced='R'):
    types = {
        41: 'STRI35', 42: 'S6', 44: 'S4R5', 45: 'S8R',
        111: 'C3D4', 112: 'C3D6', 113: 'C3D15',
        115: 'C3D8R', 116: 'C3D20R', 118: 'C3D10'
    } if reduced.upper() == 'R' else {
        41: 'STRI35', 42: 'S6', 44: 'S4R5', 45: 'S8',
        111: 'C3D4', 112: 'C3D6', 113: 'C3D15',
        115: 'C3D8', 116: 'C3D20', 118: 'C3D10'
    }

    elemdic = {k: [] for k in types}
    ls = '\n'

    UNV = UNVParser(unvfile)
    FEM = UNV.parse()

    with open(out_inp_path, 'w') as fil:
        fil.write('*NODE, NSET=NALL' + ls)
        for node in FEM.nodes:
            fil.write(f'{node.id},{node.coords[0]},{node.coords[1]},{node.coords[2]}\n')

        X_Ids = []
        for group in list(FEM.elemsets):
            if group.name.startswith('X_'):
                X_Ids.extend(group.items)
                FEM.elemsets.remove(group)
        FEM.nelemsets = len(FEM.elemsets)

        for elem in FEM.elems:
            if elem.type in types:
                elemdic[elem.type].append(elem)

        for typ, elems in elemdic.items():
            if elems:
                map_name = types[typ]
                fil.write(f'*ELEMENT,TYPE={map_name},ELSET={map_name}' + ls)
                themap = {
                    'C3D10': inp_to_med_C3D10,
                    'C3D20': inp_to_med_C3D20,
                    'S6': inp_to_med_S6,
                    'S8': inp_to_med_S8,
                    'C3D15': inp_to_med_C3D15
                }.get(map_name, list(range(1, 21)))
                for elem in elems:
                    if elem.id not in X_Ids:
                        lst = elem.cntvt
                        fil.write(f'{elem.id},')
                        for i, node_id in enumerate(themap[:elem.nnodes]):
                            fil.write(f'{lst[node_id-1]}')
                            if i < elem.nnodes - 1:
                                fil.write(',')
                        fil.write(ls)

        for group in FEM.nodesets:
            fil.write(f'*NSET,NSET={group.name}\n')
            count = 0
            lst = list(group.items)
            for i in range(group.nitems):
                count += 1
                fil.write(f'{lst.pop(0)}')
                if (count < 8) and (i < group.nitems - 1):
                    fil.write(',')
                else:
                    fil.write(ls)
                    count = 0

        for group in FEM.elemsets:
            fil.write(f'*ELSET,ELSET={group.name}\n')
            count = 0
            lst = list(group.items)
            for i in range(group.nitems):
                count += 1
                fil.write(f'{lst.pop(0)}')
                if (count < 8) and (i < group.nitems - 1):
                    fil.write(',')
                else:
                    fil.write(ls)
                    count = 0

    print(f"✅ UNV 文件 {unvfile} 成功转换为 INP 文件 {out_inp_path}")

# convert_unv_to_inp('assembled_gears.unv', 'assembled_gears_OUT.inp', "N")
