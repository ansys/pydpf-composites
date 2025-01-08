******************
PyDPF - Composites
******************

|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/badge/Python-%3E%3D3.10-blue
   :target: https://pypi.org/project/ansys-dpf-composites/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-dpf-composites.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-dpf-composites
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/ansys/pydpf-composites/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/ansys/pydpf-composites
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys/pydpf-composites/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/pydpf-composites/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


PyDPF - Composites enables the post-processing of composite structures based on
`Ansys DPF`_ and the DPF Composites plugin. So it is a Python wrapper which
implements classes on top of DPF Composites operators and data accessors for
short fiber and layered composites (layered shell and solid elements). This
module can be used to postprocess fiber reinforced plastics and layered
composites, and to implement custom failure criteria and computation. For
information demonstrating the behavior and usage of PyDPF - Composites,
see `Examples`_ in the DPF Composite documentation.

.. START_MARKER_FOR_SPHINX_DOCS

----------
Contribute
----------

Install in development mode
===========================

Installing PyDPF - Composites in development mode allows
you to modify the source and enhance it.

Before attempting to contribute to PyDPF - Composites, ensure that you are thoroughly
familiar with the `PyAnsys Developer's Guide`_.

#.  Clone the repository:

    .. code:: bash

        git clone https://github.com/ansys/pydpf-composites
        cd pydpf-composites


#.  Install dependencies:

    .. code:: bash

        python -m pip install pipx
        pipx ensurepath
        # Minimum required poetry version is 1.2.0
        pipx install poetry
        pipx install pip
        pipx install tox


    PyDPF - Composites uses `Poetry <https://python-poetry.org>`_
    to manage the development environment.

#.  Create a virtual environment and install the package with the
    development dependencies:

    .. code:: bash

        poetry install --all-extras


#.  Activate the virtual environment:

    .. code:: bash

        poetry shell


Test
====

There are different ways to run the PyDPF - Composites tests, depending on how the DPF
server is started.

#.  Run tests with a Docker container:

    Follow the steps in `Getting the DPF server Docker image`_ to get
    and run the DPF docker image. Run the tests with the following command

    .. code:: bash

        pytest . --port 50052


#.  Run tests with a DPF server started from the Ansys installer. The Ansys version must
    be 2023 R2 or later.

    .. code:: bash

        pytest . --ansys-path "C:\Program Files\Ansys Inc\v232"


#.  Run tests with a Docker container from Github (Ansys Internal only):

    .. code:: bash

        docker pull ghcr.io/ansys/pydpf-composites:latest
        pytest .


Build documentation
===================

Follow the description in `Getting the DPF server Docker image`_ image to get
and run the dpf docker image.

On Windows, build the documentation with:

.. code:: bash

    tox -e doc-windows


On Linux, build the documentation with:

.. code:: bash

    tox -e doc-linux

Ansys internal only: Build the docs with the latest container from Github:

.. code:: bash

    docker pull ghcr.io/ansys/pydpf-composites:latest
    docker run -d -p 50052:50052 -e ANSYSLMD_LICENSE_FILE=1055@mylicserver -e ANSYS_DPF_ACCEPT_LA=Y ghcr.io/ansys/pydpf-composites:latest
    tox -e doc-windows



Run style checks
================

The style checks use `pre-commit`_ and can be run through `tox`_:

.. code:: bash

    tox -e style


The style checks can also be configured to run automatically before each ``git commit``:

.. code:: bash

    pre-commit install


View documentation
-------------------
Documentation for the latest stable release of PyDPF - Composites is hosted at
`PyDPF - Composites Documentation <https://composites.dpf.docs.pyansys.com/version/stable/>`_.

In the upper right corner of the documentation's title bar, there is an option
for switching from viewing the documentation for the latest stable release
to viewing the documentation for the development version or previously
released versions.



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
.. _Examples: https://composites.dpf.docs.pyansys.com/version/stable/examples/index.html
.. _Getting the DPF server Docker image: https://composites.dpf.docs.pyansys.com/version/stable/intro.html#getting-the-dpf-server-docker-image
.. _Ansys DPF: https://dpf.docs.pyansys.com/version/stable/
