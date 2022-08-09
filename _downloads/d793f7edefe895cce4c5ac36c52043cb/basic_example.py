"""
.. _basic_example:

Basic example of dpf composites usage
-------------------------------------

Very basic!
"""

out = "Hello World"

import os

#####################
import ansys.dpf.core as dpf

# depending on your scenario you might also need to start the dpf server
# for instance server = dpf.start_local_server()
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
path = os.path.join(r"shell.rst")
model = dpf.Model(path)

dpf_server_file_path = dpf.upload_file_in_tmp_folder(path, server=server)
model = dpf.Model(dpf_server_file_path)

displacement = model.operator("U")

disp_fc = displacement.outputs.fields_container.get_data()
disp_field = disp_fc[0]

norm_op = dpf.operators.math.norm_fc()
norm_op.inputs.connect(disp_fc)

norm_op.outputs.fields_container.get_data()[0].data

model.metadata.meshed_region.plot(norm_op.outputs.fields_container.get_data()[0])
