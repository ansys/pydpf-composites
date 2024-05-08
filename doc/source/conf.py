"""Sphinx documentation configuration file."""

from datetime import datetime
import os

from ansys_sphinx_theme import ansys_favicon, get_version_match, pyansys_logo_black
import numpy as np
import pyvista
from pyvista.plotting.utilities.sphinx_gallery import DynamicScraper

from ansys.dpf.composites import __version__

# Manage errors
pyvista.set_error_output_file("errors.txt")

# Ensure that offscreen rendering is used for docs generation
pyvista.OFF_SCREEN = True

# necessary when building the sphinx gallery
pyvista.BUILDING_GALLERY = True

pyvista.global_theme.window_size = np.array([1024, 768]) * 2

# Project information
project = "ansys-dpf-composites"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
release = version = __version__

# Select desired logo, theme, and declare the html title
html_logo = pyansys_logo_black
html_favicon = ansys_favicon
html_theme = "ansys_sphinx_theme"
html_short_title = html_title = "PyDPF Composites"

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# specify the location of your github repo
cname = os.environ.get("DOCUMENTATION_CNAME", "composites.dpf.docs.pyansys.com")

html_theme_options = {
    "github_url": "https://github.com/ansys/pydpf-composites",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "switcher": {
        "json_url": f"https://{cname}/versions.json",  # noqa: E231
        "version_match": get_version_match(__version__),
    },
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
}

# Sphinx extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_gallery.gen_gallery",
    "sphinx_design",
    "pyvista.ext.viewer_directive",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/dev", None),
    "ansys-dpf-core": ("https://dpf.docs.pyansys.com/version/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    # "pyvista": ("https://docs.pyvista.org/", None),
    # "grpc": ("https://grpc.github.io/grpc/python/", None),
}
nitpick_ignore = [
    ("py:class", "NDArray"),
    ("py:class", "int64"),
]
nitpick_ignore_regex = [
    ("py:class", r"numpy\..*"),
    ("py:class", ".*FailureCriterionBase"),  # implementation detail, not documented
    # IntEnums which derive from int which has doc strings which start with lowercase.
    ("py:class", "ansys.dpf.composites.constants.Spot"),
    ("py:class", "ansys.dpf.composites.constants.Sym3x3TensorComponent"),
    ("py:class", "ansys.dpf.composites.constants.LayerProperty"),
    ("py:class", "ansys.dpf.composites.constants.LayupProperty"),
]

# sphinx_autodoc_typehints configuration
typehints_defaults = "comma"
simplify_optional_unions = False

# numpydoc configuration
numpydoc_show_class_members = False
numpydoc_xref_param_type = True

# Consider enabling numpydoc validation. See:
# https://numpydoc.readthedocs.io/en/latest/validation.html#
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # The 'GL08' check produces false positives for dataclasses whose
    # fields are documented with a docstring following their definition,
    # because this syntax doesn't set the '__doc__' attribute; but the
    # documentation renders correctly.
    # "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}


# sphinx gallery options
sphinx_gallery_conf = {
    # convert rst to md for ipynb
    "pypandoc": True,
    # path to your examples scripts
    "examples_dirs": ["../../examples"],
    # path where to save gallery generated examples
    "gallery_dirs": ["examples/gallery_examples"],
    # Pattern to search for example files
    "filename_pattern": r"\.py",
    # Remove the "Download all examples" button from the top level gallery
    "download_all_examples": False,
    # Sort gallery example by file name instead of number of lines (default)
    "within_subsection_order": "FileNameSortKey",
    # directory where function granular galleries are stored
    "backreferences_dir": None,
    # Modules for which function level galleries are created.  In
    "doc_module": "ansys-pydpf-composites",
    "image_scrapers": (DynamicScraper(), "matplotlib"),
    "ignore_pattern": r"__init__\.py",
    "thumbnail_size": (350, 350),
}

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # because we include this in examples/index.rst
    "examples/gallery_examples/index.rst",
]

# static path
html_static_path = ["_static"]

html_css_files = [
    "pydpf_composite.css",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"
