.. toctree::
   :hidden:
   :maxdepth: 3

   self
   intro
   api/index
   examples/index
   contribute

PyDPF Composites
----------------

PyDPF Composites is a Python wrapper for Ansys DPF composites. It implements
classes on top of DPF Composites operators and data accessors for short
fiber and layered composites (layered shell and solid elements). This module
can be used to postprocess fiber reinforced plastics and layered composites and
to implement custom failure criteria and computation.

.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: :octicon:`rocket` Getting started
        :link: intro
        :link-type: doc

        Contains installation instructions and a simple
        example to create a failure plot from a Workbench project.

    .. grid-item-card:: :octicon:`play` Examples
        :link: examples/index
        :link-type: doc

        Demonstrates the use of PyDPF Composites for various workflows.

    .. grid-item-card:: :octicon:`file-code` API reference
        :link: api/index
        :link-type: doc

        Describes the public Python classes, methods, and functions.

    .. grid-item-card:: :octicon:`code` Contribute
        :link: contribute
        :link-type: doc

        Provides developer installation and usage information.

Key features
''''''''''''

Here are some key features of PyDPF Composites:

* Failure criteria evaluation as shown in :ref:`Composite failure analysis <sphx_glr_examples_gallery_examples_1_failure_operator_example.py>`.
* A :class:`.SamplingPoint` class for extracting and visualizing a result over the entire thickness of a laminate as shown in
  :ref:`Sampling point <sphx_glr_examples_gallery_examples_2_sampling_point_example.py>`.
* A :class:`.ResultDefinition` class for configuring combined failure criteria and scopes.
* Accessors for getting layered properties such as plies and materials as shown in
  :ref:`Layered properties <sphx_glr_examples_gallery_examples_5_get_layup_properties_example.py>`
  and :ref:`Material properties and custom failure criterion <sphx_glr_examples_gallery_examples_4_get_material_properties_example.py>`.
* Interface to implement custom failure criteria and analysis as shown in
  :ref:`Material properties and custom failure criterion <sphx_glr_examples_gallery_examples_4_get_material_properties_example.py>`.
* Postprocessing of homogeneous elements.

Prerequisites
'''''''''''''

Here are some prerequisites for PyDPF Composites:

- Installation of `Ansys Workbench`_ 2023 R1 or later. For more information,
  see `Compatibility`_ in the DPF help.
- ACP model or short fiber composite model.

Limitations
'''''''''''
- Layered elements (section data) that have not been preprocessed with ACP are not supported.
  For information on converting legacy models, see `Import of Legacy Mechanical APDL Composite Models`_
  in the Ansys Help.
- Only the Mechanical APDL solver is supported.


.. _Ansys Workbench: https://download.ansys.com/Current%20Release
.. _Import of Legacy Mechanical APDL Composite Models: https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v231/en/acp_ug/acp_import_legacy_APDL_comp.html
.. _Compatibility: https://dpf.docs.pyansys.com/getting_started/compatibility.html
