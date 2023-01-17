Material Properties
-------------------
A note on material ids: In the pydpf-composites module,
materials are reference by their dpf_material_id. The dpf_material_id
is generated based on the materials present in the result file.
The dpf_material_id can be different from the material id used in the solver.
:class:`~ansys.dpf.composites.ElementInfo` contains the dpf_material_id for the materials
of a given element. The dpf_material_id for a given analysis ply can be obtained
by calling :func:`~ansys.dpf.composites.get_dpf_material_id_by_analyis_ply_map`. A lookup by
material name is currently not available.
The :ref:`sphx_glr_examples_gallery_examples_4_get_material_properties_example.py`
example shows how to evaluate material properties.

.. currentmodule:: ansys.dpf.composites

.. autosummary::
    :toctree: _autosummary

    get_constant_property
    get_all_dpf_material_ids
    get_constant_property_dict
    MaterialProperty