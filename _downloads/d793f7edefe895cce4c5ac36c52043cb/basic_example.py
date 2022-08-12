"""
.. _basic_example:

Basic example of dpf composites usage
-------------------------------------

Very basic!
"""


import json
import os

#####################
import ansys.dpf.core as dpf


def get_failure_criteria_definition():
    max_strain_json_configuration = {
        "active": True,
        "e1": True,
        "e12": True,
        "e13": False,
        "e2": True,
        "e23": False,
        "e3": False,
        "eSxy": 0.015,
        "eSxz": 0.015,
        "eSyz": 0.015,
        "eXc": -0.008,
        "eXt": 0.01,
        "eYc": -0.008,
        "eYt": 0.01,
        "eZc": -0.008,
        "eZt": 0.01,
        "force_global_strain_limits": False,
        "wf_e1": 1,
        "wf_e12": 1,
        "wf_e13": 1,
        "wf_e2": 1,
        "wf_e23": 1,
        "wf_e3": 1,
    }
    max_stress_json_configuration_2d = {
        "active": True,
        "s1": True,
        "s12": True,
        "s13": False,
        "s2": True,
        "s23": False,
        "s3": False,
        "wf_s1": 1,
        "wf_s12": 1,
        "wf_s13": 1,
        "wf_s2": 1,
        "wf_s23": 1,
        "wf_s3": 1,
    }
    quadratic_failure_json_configuration_2d = {"active": True, "dim": 2, "wf": 1}
    hashin_json_configuration = {
        "active": True,
        "dim": 2,
        "hd": True,
        "hf": True,
        "hm": True,
        "wf_hd": 1.0,
        "wf_hf": 1.0,
        "wf_hm": 1.0,
    }
    cuntze_failure_json_configuration = {
        "active": True,
        "b21": 0.2,
        "b32": 1.38,
        "cfc": True,
        "cft": True,
        "cma": True,
        "cmb": True,
        "cmc": True,
        "dim": 2,
        "fracture_plane_angle": 53,
        "mode_interaction_coeff": 2.6,
        "wf_cfc": 1,
        "wf_cft": 1,
        "wf_cma": 1,
        "wf_cmb": 1,
        "wf_cmc": 1,
    }

    core_failure_json_configuration = {"active": True, "include_ins": False, "wf": 1}

    von_mises_only_strain_json_configuration = {
        "active": True,
        "vme": True,
        "vms": False,
        "wf_vme": 1.0,
        "wf_vms": 1.0,
    }

    return {
        "max_strain": max_strain_json_configuration,
        "max_stress": max_stress_json_configuration_2d,
        "hashin": hashin_json_configuration,
        "tsai_hill": quadratic_failure_json_configuration_2d,
        "tsai_wu": quadratic_failure_json_configuration_2d,
        "hoffman": quadratic_failure_json_configuration_2d,
        "core_failure": core_failure_json_configuration,
        "von_mises": von_mises_only_strain_json_configuration,
        "cuntze": cuntze_failure_json_configuration,
    }


def get_pin_config():
    return {
        "input": {
            "data_source": 4,
            "property": 13,
            "mesh_region": 7,
            "configuration": 100,
            "strains": 0,
            "stresses": 1,
            "materials_container": 23,
            "material_support": 21,
        },
        "output": {
            "min": 0,
            "max": 1,
            "mode_index": 0,
            "value_index": 1,
        },
    }


# depending on your scenario you might also need to start the dpf server
# for instance server = dpf.start_local_server()
server = dpf.server.connect_to_server("127.0.0.1", port=21002)
dpf.load_library("libcomposite_operators.so", "composites")
dpf.load_library("libAns.Dpf.EngineeringData.so", "engineeringdata")

rst_path = os.path.join(r"shell.rst")
h5_path = os.path.join(r"ACPCompositeDefinitions.h5")
material_path = os.path.join(r"material.engd")

rst_server_path = dpf.upload_file_in_tmp_folder(rst_path, server=server)
h5_server_path = dpf.upload_file_in_tmp_folder(h5_path, server=server)
material_server_path = dpf.upload_file_in_tmp_folder(material_path, server=server)
model = dpf.Model(rst_server_path)


pin_config = get_pin_config()
out_pins = pin_config["output"]
in_pins = pin_config["input"]


rst_path = rst_server_path
eng_data_path = material_server_path
composite_definitions_path = h5_server_path

rst_data_source = dpf.DataSources(rst_path)

mesh_provider = dpf.Operator("MeshProvider")
mesh_provider.connect(in_pins["data_source"], rst_data_source)
mesh_provider.run()

eng_data_source = dpf.DataSources()
eng_data_source.add_file_path(eng_data_path, "EngineeringData")

composite_definitions_source = dpf.DataSources()
composite_definitions_source.add_file_path(composite_definitions_path, "CompositeDefinitions")

material_support_provider = dpf.Operator("support_provider")
material_support_provider.connect(in_pins["property"], "mat")
material_support_provider.connect(in_pins["data_source"], rst_data_source)
material_support_provider.run()

result_info_provider = dpf.Operator("ResultInfoProvider")
result_info_provider.connect(in_pins["data_source"], rst_data_source)

material_provider = dpf.Operator("eng_data::ans_mat_material_provider")
material_provider.connect(in_pins["data_source"], eng_data_source)
material_provider.connect(1, result_info_provider, 0)
material_provider.connect(0, material_support_provider, 0)
material_provider.run()

layup_provider = dpf.Operator("composite::layup_provider_operator")
mesh_provider = dpf.Operator("MeshProvider")
mesh_provider.connect(in_pins["data_source"], rst_data_source)
mesh_provider.run()

layup_provider.connect(in_pins["mesh_region"], mesh_provider, 0)
layup_provider.connect(in_pins["data_source"], composite_definitions_source)
layup_provider.connect(in_pins["material_support"], material_support_provider, 0)
layup_provider.connect(3, result_info_provider, 0)
layup_provider.run()

material_provider.connect(0, material_support_provider, 0)
material_provider.connect(in_pins["data_source"], eng_data_source)

material_provider.run()

failure_criteria_definition = get_failure_criteria_definition()

strain_operator = dpf.Operator("EPEL")
strain_operator.connect(in_pins["data_source"], rst_data_source)
strain_operator.connect(5, False)

stress_operator = dpf.Operator("S")
stress_operator.connect(in_pins["data_source"], rst_data_source)
stress_operator.connect(5, False)

failure_evaluator = dpf.Operator("composite::multiple_failure_criteria_operator")
failure_evaluator.connect(in_pins["configuration"], json.dumps(failure_criteria_definition))
failure_evaluator.connect(in_pins["materials_container"], material_provider, 0)
failure_evaluator.connect(in_pins["strains"], strain_operator, 0)
failure_evaluator.connect(in_pins["stresses"], stress_operator, 0)
failure_evaluator.connect(in_pins["mesh_region"], mesh_provider, 0)

minmax_per_element = dpf.Operator("composite::minmax_per_element_operator")
minmax_per_element.connect(0, failure_evaluator, 0)
minmax_per_element.connect(in_pins["mesh_region"], mesh_provider, 0)
minmax_per_element.connect(in_pins["material_support"], material_support_provider, 0)

output = minmax_per_element.get_output(out_pins["max"], dpf.types.fields_container)

######################################################################################
model.metadata.meshed_region.plot(output[out_pins["value_index"]])
