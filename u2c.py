from unv2calculix import convert_unv_to_inp


def convert_u2c(unv_file_name='assembled_gears.unv',inp_file_name='assembled_gears_OUT.inp'):
    convert_unv_to_inp(unv_file_name, inp_file_name, "N")
    return