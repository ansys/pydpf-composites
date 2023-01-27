****************
PyDPF Composites
****************
-----------------
Developer's Guide
-----------------
|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/badge/Python-%3E%3D3.7-blue
   :target: https://pypi.org/project/pydpf-composites/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/pydpf-composites.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/pydpf-composites
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


A Python wrapper for Ansys DPF Composites. It implements classes on top of the
DPF Composites operators and data accessors for short fiber and layered composites
(layered shell and solid elements). This module can be used to post-process these structures,
and to implement custom failure criteria and computation.
For instance fatigue analysis. See `PyDPF Composites - Examples`_.

Developer setup
===============

Installing PyDPF Composites in developer mode allows
you to modify the source and enhance it.

Before contributing to the project, please refer to the `PyAnsys Developer's guide`_.

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
    dependencies.
    PyDPF Composites uses `poetry <https://python-poetry.org>`_ to manage the
    development environment.

    .. code:: bash

        poetry install --all-extras

#.  Activate the virtual environment:

    .. code:: bash

        poetry shell

Testing
=======
#.  Run tests with a docker container. Note: the docker container is not yet publicly available.

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:231
        pytest .

#.  Run tests with a DPF Server started from the Ansys installer (needs at least version 2023 R1):

    .. code:: bash

        pytest . --ansys-path "C:\Program Files\Ansys Inc\v231"

#.  Run tests with a local Grpc server executable:

    .. code:: bash

        pytest . --server-bin dpf_composites/bin/lib/deps/Ans.Dpf.Grpc.exe

    This currently works only on windows and with the directory structure of dpf_composites (an internal ansys package). The runtime dependencies of Ans.Dpf.Grpc.exe have to be in its folder and the parent folder.


Build documentation
===================
#.  Windows:

    Note: the docker container is not yet publicly available.

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:231
        docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:231
        tox -e doc-windows

#.  Linux:

    Note: the docker container is not yet publicly available.

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:231
        docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:231
        tox -e doc-linux

Run style checks
================

The style checks use `pre-commit`_, and can be run through `tox`_:

.. code:: bash

    tox -e style

The style checks can also be configured to run automatically before each ``git commit``,
with

.. code:: bash

    pre-commit install

.. LINKS AND REFERENCES
.. _black: https://github.com/psf/black
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _isort: https://github.com/PyCQA/isort
.. _pip: https://pypi.org/project/pip/
.. _pre-commit: https://pre-commit.com/
.. _PyAnsys Developer's guide: https://dev.docs.pyansys.com/
.. _pytest: https://docs.pytest.org/en/stable/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _tox: https://tox.wiki/
.. _PyDPF Composites - Examples: https://composites.dpf.docs.pyansys.com/dev/examples/index.html
