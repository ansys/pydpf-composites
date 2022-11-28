.. _select_indices:

Select Elementary Indices
-------------------------

This module provides functions to filter elementary data.
A layered element has

    num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane

elementary data points. number_of_spots indicates the number of through-the-thickness integration points per layer. number_of_spots is controlled
by the keyoption 8 which indicates how much output is written (e.g. only 'bottom' and 'top' or 'bottom', 'top' and 'mid').
Each elementary data point can have multiple components (e.g 1 component for scalar data or 6 components for
symmetrical 3x3 tensors). The elementary data of an element is available as a 2D vector with shape
(num_elementary_data, number_of_components).

Here are some examples:

* Stress output for a Layered Shell Element (181, four Nodes) with 5 layers and keyoption 8 = 2 (write output for 'bot', 'top' and 'mid')

    * number_of_layers = 5
    * number_of_spots = 3 ('bot', 'top', 'mid')
    * number_of_nodes_per_spot_plane = 4 (equal to number of nodes)
    * number_of_components = 6

    => num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane = 60

* Stress output for a Layered Solid Element (185, 8 Nodes) with 7 layers and keyoption 8 = 1 (write output for 'bot', 'top')

    * number_of_layers = 7
    * number_of_spots = 2 ('bot', 'top')
    * number_of_nodes_per_spot_plane = 4
    * number_of_components = 6

    => num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane = 56

The functions in this module compute an array of elementary indices for a given selection of
layers, nodes, spots, material_ids or analysis plies. These elementary indices can be used to index the first axis
of the elementary data array. Please check the :ref:`sphx_glr_examples_gallery_examples_filter_composite_data_example.py` section for complete usage examples.


.. currentmodule:: ansys.dpf.composites

.. autosummary::
    :toctree: _autosummary

    get_selected_indices
    get_selected_indices_by_material_ids
    get_selected_indices_by_analysis_ply