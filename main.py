import gear_assemble
import mesh_make
import u2c
import surface_make

gear_assemble.assemble_gear(gear1_file_name="gear_step/SpurGear1.STEP",gear2_file_name="gear_step/SpurGear2.STEP")
mesh_make.make_mesh()
u2c.convert_u2c()
surface_make.make_surface("contact_1")
surface_make.make_surface("contact_2")