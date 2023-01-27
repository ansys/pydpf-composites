.. toctree::
   :hidden:
   :maxdepth: 3

   self
   intro
   api/index
   examples/index
   Developer's Guide <developers_guide>

PyDPF Composites
----------------

A Python wrapper for Ansys DPF composites. It implements classes on top of the
DPF Composites operators and data accessors for short fiber and layered composites
(layered shell and solid elements). This module can be used to post-process fiber
reinforced plastics and layered composites, and to implement custom failure
criteria and computation.

.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: :octicon:`rocket` Getting started
        :link: intro
        :link-type: doc

        The getting started guide contains installation instructions, and a simple
        example to create a failure plot from a Workbench project.

    .. grid-item-card:: :octicon:`play` Examples
        :link: examples/index
        :link-type: doc

        The examples demonstrate the use of PyDPF Composites for various workflows.

    .. grid-item-card:: :octicon:`file-code` API reference
        :link: api/index
        :link-type: doc

        Reference for the public Python classes, methods and functions.

    .. grid-item-card:: :octicon:`code` Developer's guide
        :link: developers_guide
        :link-type: doc

        Contributing to PyDPF Composites.

Key features
''''''''''''

* Failure criteria evaluator.
  See this :doc:`Example </examples/gallery_examples/1_failure_operator_example>`.
* :doc:`Sampling Point <api/_autosummary/ansys.dpf.composites.sampling_point.SamplingPoint>` to extract and visualize result over the
  entire thickness of the laminate.
  :doc:`Here <examples/gallery_examples/2_sampling_point_example>` is an example.
* :doc:`Result Definition <api/_autosummary/ansys.dpf.composites.result_definition.ResultDefinition>` to configure combined failure criteria and scopes.
* Accessors to lay-up data such as plies and materials. Refer to the examples
  :doc:`Lay-up Properties <examples/gallery_examples/5_get_layup_properties_example>`
  and :doc:`Material Properties <examples/gallery_examples/4_get_material_properties_example>`.
* Interface to implement custom failure criteria and analysis as shown in this
  :doc:`Example <examples/gallery_examples/4_get_material_properties_example>`.
* Post-processing of homogeneous elements.

Pre-requisites and compatibility
''''''''''''''''''''''''''''''''
- Installation of `Ansys Workbench`_.
- ACP model or short fiber composite model.
- PyDPF Composites supports Ansys 2023 R1 or newer. More details can be found on
  the DPF help about `Compatibility`_.

Limitations
'''''''''''
- Layered elements (section data) which have not been pre-processed with ACP are not supported.
  Refer to the Section `Import Legacy Models`_ on the official Ansys help
  to learn how to convert legacy models.
- Other solvers than MAPDL are not supported.

.. _Ansys Workbench: https://download.ansys.com/Current%20Release
.. _Import Legacy Models: https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v231/en/acp_ug/acp_import_legacy_APDL_comp.html
.. _Compatibility: https://dpf.docs.pyansys.com/getting_started/compatibility.html
