.. _layup_information_classes:

Lay-up information
------------------
General features to access information on the composite lay-up.

.. module:: ansys.dpf.composites.layup_info

.. autosummary::
    :toctree: _autosummary

    add_layup_info_to_mesh
    get_element_info_provider
    get_dpf_material_id_by_analyis_ply_map
    AnalysisPlyInfoProvider
    ElementInfoProvider
    ElementInfo
    LayerProperty
    LayupPropertiesProvider
    LayupProperty


Material properties
'''''''''''''''''''
A note on material ids: in the PyDPF Composites module,
materials are reference by their ``dpf_material_id``. The ``dpf_material_id``
is generated based on the materials present in the result file.
The ``dpf_material_id`` can be different from the material id used in the solver.
:class:`~ElementInfo` contains the ``dpf_material_id`` for the materials
of a given element. The ``dpf_material_id`` for a given analysis ply can be obtained
by calling :func:`~get_dpf_material_id_by_analyis_ply_map`. A lookup by
material name is currently not available.
The :ref:`sphx_glr_examples_gallery_examples_4_get_material_properties_example.py`
example shows how to evaluate material properties.

.. module:: ansys.dpf.composites.layup_info.material_properties

.. autosummary::
    :toctree: _autosummary

    MaterialProperty
    get_constant_property
    get_all_dpf_material_ids
    get_constant_property_dict


Material operators
''''''''''''''''''

.. module:: ansys.dpf.composites.layup_info.material_operators

.. autosummary::
    :toctree: _autosummary

    MaterialOperators
    get_material_operators
