.. toctree::
   :hidden:
   :maxdepth: 3

   self
   intro
   api/index
   examples/index
   Developer's Guide <developers_guide>

pyDPF Composites
----------------

A Python wrapper for Ansys dpf composites. It implements classes on top of the
DPF Composites operators and data accessors for short fiber and layered composites
(layered shell and solid elements). This module can be used to post-process fiber
reinforced plastics and layered composites, and to implement custom failure
criteria and computation.

.. grid:: 1 1 2 2
    :gutter: 2

    .. grid-item-card:: :octicon:`rocket` Getting Started
        :link: intro
        :link-type: doc

        Installation, load model and failure plot.

    .. grid-item-card:: :octicon:`play` Examples
        :link: examples/index
        :link-type: doc

        Collection of examples.

    .. grid-item-card:: :octicon:`file-code` API Reference
        :link: api/index
        :link-type: doc

        Reference for the public Python classes, methods and functions.

    .. grid-item-card:: :octicon:`code` Developer's Guide
        :link: developers_guide
        :link-type: doc

        Contributing to pyDPF Composites.

Key features
''''''''''''

* Failure criteria evaluator.
  See this :doc:`Example </examples/gallery_examples/failure_operator_example>`.
* :doc:`Sampling Point <api/_autosummary/ansys.dpf.composites.SamplingPoint>` to
  extract and visualize result over the entire thickness of the laminate.
  :doc:`Here <examples/gallery_examples/sampling_point_example>` is an example.
* :doc:`Result Definition <api/_autosummary/ansys.dpf.composites.ResultDefinition>` to configure
  combined failure criteria and scopes.
* Exposure of material properties (elasticity, strength limits et).
* Accessors to extract ply-wise results and material properties.
