.. _select_indices:

Select elementary indices
-------------------------

This module provides functions to filter elementary data.
A layered element has the following number of elementary data points:

.. code::

    num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane

In the preceding definition, ``number_of_spots`` indicates the number of through-the-thickness
integration points per layer. ``number_of_spots`` is controlled by ``keyoption 8``, which
indicates how much output is written. For example, you might write output for only ``'bottom'``
and ``'top'`` or for ``'bottom'``, ``'top'``, and ``'mid'``.

Each elementary data point can have multiple components. For example, it might have one component
for scalar data or six components for symmetrical 3x3 tensors. The elementary data of an element
is available as a 2D vector with shape ``(num_elementary_data, number_of_components)``.

Here are some examples:

* Get the stress output for a layered shell element (181, four nodes) with five layers and
  ``keyoption 8 = 2``. Write the output for ``'bot'``, ``'top'``, and ``'mid'``.

  * ``number_of_layers`` = 5
  * ``number_of_spots`` = 3 (bottom, top, and mid)
  * ``number_of_nodes_per_spot_plane`` = 4 (equal to number of nodes)
  * ``number_of_components`` = 6

  Thus, ``num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane``
  = 60.

* Get the stress output for a layered solid element (185, eight nodes) with seven layers and
  ``keyoption 8 = 1``. Write the output for ``'bot'`` and ``'top'``.

  * ``number_of_layers`` = 7
  * ``number_of_spots`` = 2 (bottom and top)
  * ``number_of_nodes_per_spot_plane`` = 4
  * ``number_of_components`` = 6

  Thus, ``num_elementary_data = number_of_layers * number_of_spots * number_of_nodes_per_spot_plane``
  = 56.

The functions in this module compute an array of elementary indices for a given selection of
layers, nodes, spots, DPF material IDs, or analysis plies. These elementary indices can be used
to index the first axis of the elementary data array. For usage information, see
:ref:`sphx_glr_examples_gallery_examples_6_filter_composite_data_example.py`.


.. module:: ansys.dpf.composites.select_indices

.. autosummary::
    :toctree: _autosummary

    get_selected_indices
    get_selected_indices_by_analysis_ply
    get_selected_indices_by_dpf_material_ids
