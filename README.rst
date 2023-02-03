****************
PyDPF Composites
****************

|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/badge/Python-%3E%3D3.7-blue
   :target: https://pypi.org/project/ansys-dpf-composites/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-dpf-composites.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-dpf-composites
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/pyansys/pydpf-composites/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/pyansys/pydpf-composites
   :alt: Codecov

.. |GH-CI| image:: https://github.com/pyansys/pydpf-composites/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/pyansys/pydpf-composites/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


PyDPF Composites is a Python wrapper for Ansys DPF composites. It implements
classes on top of DPF Composites operators and data accessors for short
fiber and layered composites (layered shell and solid elements). This module
can be used to postprocess fiber reinforced plastics and layered composites and
to implement custom failure criteria and computation. For examples demonstrating
the behavior and usage of PyDPF Composites, see `PyDPF Composites - Examples`_.

.. START_MARKER_FOR_SPHINX_DOCS

----------
Contribute
----------

Install in development mode
===========================

Installing PyDPF Composites in development mode allows
you to modify the source and enhance it.

Before attempting to contribute to PyDPF Composites, ensure that you are thoroughly
familiar with the `PyAnsys Developer's Guide`_.

#.  Clone the repository:

    .. code:: bash

        git clone https://github.com/pyansys/pydpf-composites
        cd pydpf-composites


#.  Install dependencies:

    .. code:: bash

        python -m pip install pipx
        pipx ensurepath
        # Minimum required poetry version is 1.2.0
        pipx install poetry
        pipx install pip
        pipx install tox


#.  Create a virtual environment and install the package with development
    dependencies. PyDPF Composites uses `Poetry <https://python-poetry.org>`_
    to manage the development environment.

    .. code:: bash

        poetry install --all-extras


#.  Activate the virtual environment:

    .. code:: bash

        poetry shell


Test
====

.. note::

   The Docker container referenced in the first option is not yet publicly available.

There are three ways to run the PyDPF Composites tests, depending on how the DPF
server is started.

#.  Run tests with a Docker container.

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:231
        pytest .


#.  Run tests with a DPF server started from the Ansys installer. The Ansys version must
    be 2023 R1 or later.

    .. code:: bash

        pytest . --ansys-path "C:\Program Files\Ansys Inc\v231"


#.  Run tests with a local gRPC server executable:

    .. code:: bash

        pytest . --server-bin dpf_composites/bin/lib/deps/Ans.Dpf.Grpc.exe


    This currently works only on Windows and with the directory structure of the Ansys internal
    ``dpf_composites`` package. The runtime dependencies of the ``Ans.Dpf.Grpc.exe`` file must be
    in its folder and the parent folder.


Build documentation
===================

.. note::

    The Docker container referenced in this section is not yet publicly available.


On Windows, build documentation with this code:

.. code:: bash

    docker pull ghcr.io/pyansys/pydpf-composites:231
    docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:231
    tox -e doc-windows


On Linux, build documentation with this code:

.. code:: bash

    docker pull ghcr.io/pyansys/pydpf-composites:231
    docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:231
    tox -e doc-linux


Run style checks
================

The style checks use `pre-commit`_ and can be run through `tox`_:

.. code:: bash

    tox -e style


The style checks can also be configured to run automatically before each ``git commit``:

.. code:: bash

    pre-commit install


.. LINKS AND REFERENCES
.. _black: https://github.com/psf/black
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _isort: https://github.com/PyCQA/isort
.. _pip: https://pypi.org/project/pip/
.. _pre-commit: https://pre-commit.com/
.. _PyAnsys Developer's Guide: https://dev.docs.pyansys.com/
.. _pytest: https://docs.pytest.org/en/stable/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _tox: https://tox.wiki/
.. _PyDPF Composites - Examples: https://composites.dpf.docs.pyansys.com/dev/examples/index.html
