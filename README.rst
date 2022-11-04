Pydpf composites
================
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


A Python wrapper for Ansys dpf composites


    
Developer Setup
^^^^^^^^^^^^^^^^

Installing Pydpf composites in developer mode allows
you to modify the source and enhance it.

Before contributing to the project, please refer to the `PyAnsys Developer's guide`_.

#. Clone the repository:

    .. code:: bash

        git clone https://github.com/pyansys/pydpf-composites
        cd pydpf-composites


#. Install dependencies:

    .. code:: bash

        python -m pip install pipx
        pipx ensurepath
        pipx install poetry
        pipx instal pip
        pipx install tox




Testing
--------------
#. Run tests with a docker container:

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:latest
        pytest .

#. Run tests with a local Grpc server executable:

    .. code:: bash

        pytest . --server-bin dpf_composites/bin/lib/deps/Ans.Dpf.Grpc.exe

This currently works only on windows and with the directory structure of dpf_composites. (The runtime dependencies of Ans.Dpf.Grpc.exe have to be in its folder and the parent folder)


Build documentation
^^^^^^^^^^^^^^^^^^^

#. Windows:

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:latest
        docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:latest
        tox -e doc-windows

#. Linux:

    .. code:: bash

        docker pull ghcr.io/pyansys/pydpf-composites:latest
        docker run -d -p 21002:50052  ghcr.io/pyansys/pydpf-composites:latest
        tox -e doc-linux



Run style checks
^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    tox -e style




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
