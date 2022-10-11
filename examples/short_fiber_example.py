"""
.. _short_fiber_example:

Basic example for a short fiber failure analysis
------------------------------------------------


"""
import os
import pathlib

# %%
# Load ansys libraries
import ansys.dpf.core as dpf

from ansys.dpf.composites.load_plugin import load_composites_plugin

# %%
# Load dpf plugin
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
load_composites_plugin()

# %%
# Specify input files and upload them to the server

TEST_DATA_ROOT_DIR = pathlib.Path(os.environ["REPO_ROOT"]) / "tests" / "data" / "short_fiber"

engd_file_path = os.path.join(TEST_DATA_ROOT_DIR, "MatML.xml")
rst_path = os.path.join(TEST_DATA_ROOT_DIR, "file.rst")
dat_file_path = os.path.join(TEST_DATA_ROOT_DIR, "ds.dat")

rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=server)
dat_file_path_server_path = dpf.upload_file_in_tmp_folder(dat_file_path, server=server)
engd_file_path_server_path = dpf.upload_file_in_tmp_folder(engd_file_path, server=server)

# %%
# Setup data sources
data_sources = dpf.DataSources()
data_sources.add_file_path(engd_file_path_server_path, "EngineeringData")
data_sources.add_file_path(dat_file_path_server_path, "dat")
data_sources.set_result_file_path(rst_server_path)

# %%
# Create dpf model and mesh provider
model = dpf.Model(rst_server_path)

# %%
# Short Fiber Failure Criterion Evaluator
sf_op = dpf.Operator("composite::short_fiber_failure_criterion_evaluator")
sf_op.inputs.data_sources(data_sources)
sf_op.inputs.stress_limit_type("ultimate")  # "yield" or "ultimate" (default)
sf_op.run()

mat_support_operator = dpf.Operator("mat_support_provider")
mat_support_operator.connect(4, data_sources)

minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.inputs.fields_container(sf_op)
minmax_per_element.inputs.mesh(model.metadata.meshed_region)
minmax_per_element.inputs.abstract_field_support(mat_support_operator)
max_element_stress_cont = minmax_per_element.get_output(1, dpf.types.fields_container)
fc_mode = max_element_stress_cont[0]
fc_value = max_element_stress_cont[1]
mesh = model.metadata.meshed_region
mesh.plot(fc_value, show_edges=True)
