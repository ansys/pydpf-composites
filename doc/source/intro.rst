Getting started
---------------

Installation
^^^^^^^^^^^^

PyDPF Composites supports Ansys version 2023 R1 and later. Make sure you have a licensed copy of Ansys installed. See
:ref:`Compatibility` to understand which ``ansys-dpf-composites`` version corresponds to which Ansys version.

Install the ``ansys-dpf-composites`` package with ``pip``:

.. code::

    pip install ansys-dpf-composites

Specific versions can be installed by specifying the version in the pip command. For example: Ansys 2023 R1 requires ansys-dpf-composites version 0.1.0:

.. code::

    pip install ansys-dpf-composites==0.3.0


You should use a `virtual environment <https://docs.python.org/3/library/venv.html>`_,
because it keeps Python packages isolated from your system Python.


Examples
^^^^^^^^

The :doc:`examples/index` section provides these basic examples for getting started:

* :ref:`sphx_glr_examples_gallery_examples_001_failure_operator_example.py`
* :ref:`sphx_glr_examples_gallery_examples_002_sampling_point_example.py`

At the end of each example, there is a button for downloading the example's Python source code.
Input files, such as the results file and composite definition, are downloaded from a Git
repository when running the example.

For larger models, initializing the :class:`.CompositeModel` class can be slow because it
automatically creates many different providers that are not needed in all workflows.
Consider using the :ref:`Lay-up information <layup_information_classes>` classes directly.

Start from a local Ansys Workbench project
""""""""""""""""""""""""""""""""""""""""""

To get started on a local Ansys Workbench project, first determine the result folder by
right-clicking the solution object in Ansys Mechanical and selecting **Open Solver Files Directory**.
Then call the :func:`.get_composite_files_from_workbench_result_folder` function with this folder.

This code shows how to set up a project from Workbench, create a basic failure plot, and display
detailed output for a sampling point:

.. code::

    from ansys.dpf.composites.composite_model import CompositeModel
    from ansys.dpf.composites.constants import FailureOutput
    from ansys.dpf.composites.data_sources import get_composite_files_from_workbench_result_folder
    from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
    from ansys.dpf.composites.server_helpers import connect_to_or_start_server

    # Folder that opens after clicking "Open Solver Files Directory"
    result_folder = r"D:\simulations\my_simulation_files\dp0\SYS\MECH"

    # Create the composite files object that contains
    # the results file, the material properties file, and the
    # composite definitions
    composite_files = get_composite_files_from_workbench_result_folder(result_folder)

    # Start the server. By default this starts
    # a new local server and loads the composites plugin
    server = connect_to_or_start_server()

    # Create a composite model
    composite_model = CompositeModel(composite_files, server)

    # Evaluate combined failure criterion
    combined_failure_criterion = CombinedFailureCriterion(failure_criteria=[MaxStressCriterion()])
    failure_result = composite_model.evaluate_failure_criteria(combined_failure_criterion)

    irf_field = failure_result.get_field({"failure_label": FailureOutput.FAILURE_VALUE})
    irf_field.plot()

    # Show sampling point for element with id/label 1
    element_id = 1
    sampling_point = composite_model.get_sampling_point(
        combined_criterion=combined_failure_criterion, element_id=element_id
    )

    plots = sampling_point.get_result_plots()
    plots.figure.show()


.. image:: _static/boat_irf.png
  :width: 750
  :alt: IRF plot on boat

.. image:: _static/boat_sampling_point.png
  :width: 750
  :alt: Sampling point on boat

.. _Compatibility:

Compatibility
"""""""""""""

The following table shows which ``ansys-dpf-composites`` version is compatible with which server version (Ansys version). See :ref:`Get DPF Docker image` to get the pre-releases.
By default the DPF server is started from the latest Ansys installer. To choose a specific Ansys version or connect to an existing server, use the appropriate arguments for  :func:`.connect_to_or_start_server`

.. list-table::
   :widths: 20 20
   :header-rows: 1

   * - Server version
     - ansys.dpf.composites Python module version
   * - 8.1 (Ansys 2024 R2 pre1)
     - 0.3.0 and later
   * - 8.0 (Ansys 2024 R2 pre0)
     - 0.3.0 and later
   * - 7.0 (Ansys 2024 R1)
     - 0.3.0 and later
   * - 7.0 (Ansys 2024 R1 pre0)
     - 0.3.0 and later
   * - 6.2 (Ansys 2023 R2)
     - 0.2.0 and 0.3
   * - 6.1 (Ansys 2023 R2 pre1)
     - 0.2.0 and 0.3
   * - 6.0 (Ansys 2023 R2 pre0)
     - Not available. The composites plugin is not part of the Ansys 2023 R2 pre0 release.
   * - 5.0 (Ansys 2023 R1)
     - 0.1.0


.. _Get DPF Docker image:

Getting the DPF server Docker image
"""""""""""""""""""""""""""""""""""
Follow the steps described in the DPF documentation in the section `Run DPF Server in A Docker Container <https://dpf.docs.pyansys.com/version/stable/user_guide/getting_started_with_dpf_server.html#run-dpf-server-in-a-docker-container>`_.
Make sure you also download the composites plugin (e.g ``ansys_dpf_composites_lin_v2024.1.pre0.zip``).
After following the preceding steps, you should have a running DPF Docker container that listens to port 50052.
