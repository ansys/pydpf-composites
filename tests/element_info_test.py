# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import pathlib

from ansys.dpf.core import unit_systems
import numpy as np
import pytest

from ansys.dpf.composites.composite_model import CompositeModel, CompositeScope
from ansys.dpf.composites.data_sources import (
    CompositeDefinitionFiles,
    ContinuousFiberCompositesFiles,
)
from ansys.dpf.composites.failure_criteria import CombinedFailureCriterion, MaxStressCriterion
from ansys.dpf.composites.result_definition import FailureMeasureEnum
from ansys.dpf.composites.server_helpers import version_older_than

SEPARATOR = "::"


def test_section_definitions_from_multiple_sources(dpf_server):
    """
    This model has sections from the RST, ACP lay-up definition are supported.

    Element 1: lay-up from ACP
    Element 2: section from MAPDL / RST
    Element 3: section from MAPDL with one layer which has material 0. So
    the material ID from the EBLOCK must be used. The test ensures that
    the element provider handles this correctly.
    """
    if version_older_than(dpf_server, "8.0"):
        pytest.xfail("Section data from RST is supported since server version 8.0 (2024 R2).")

    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "shell_mixed_acp_rst_model"

    files = ContinuousFiberCompositesFiles(
        rst=os.path.join(TEST_DATA_ROOT_DIR, "linear_shell_with_MAPDL_sections.rst"),
        composite={
            "shell": CompositeDefinitionFiles(
                definition=os.path.join(TEST_DATA_ROOT_DIR, "linear_shell_with_MAPDL_sections.h5"),
                mapping=None,
            )
        },
        engineering_data=os.path.join(TEST_DATA_ROOT_DIR, "material.engd"),
        files_are_local=True,
    )

    composite_model = CompositeModel(
        files, server=dpf_server, default_unit_system=unit_systems.solver_nmm
    )

    ud_mat_id = composite_model.material_names["Epoxy Carbon UD (230 GPa) Wet"]
    woven_mat_id = composite_model.material_names["Epoxy Carbon Woven (230 GPa) Prepreg"]
    element_1 = composite_model.get_element_info(1)
    assert element_1.is_layered
    assert all(
        element_1.dpf_material_ids
        == np.array([ud_mat_id, ud_mat_id, woven_mat_id, woven_mat_id, ud_mat_id, ud_mat_id])
    )
    element_2 = composite_model.get_element_info(2)
    assert element_2.is_layered
    assert all(element_2.dpf_material_ids == np.array([woven_mat_id, ud_mat_id, woven_mat_id]))
    element_3 = composite_model.get_element_info(3)
    assert element_3.is_layered
    assert all(element_3.dpf_material_ids == np.array([ud_mat_id]))

    combined_failure_criterion = CombinedFailureCriterion(
        "max stress", failure_criteria=[MaxStressCriterion()]
    )

    for v in FailureMeasureEnum:
        failure_output = composite_model.evaluate_failure_criteria(
            combined_criterion=combined_failure_criterion,
            composite_scope=CompositeScope(),
            measure=v,
        )


def test_element_info_for_homogeneous_solids_and_beams(dpf_server):
    """
    This model has beam elements, layered shells with ACP composite definitions and
    homogeneous solids (without sections).

    Element 1 to 8: homogeneous solids
    Element 33 - 57: layered shells
    Element 58 - 61: beams
    """
    if version_older_than(dpf_server, "8.0"):
        pytest.xfail("Section data from RST is supported since server version 8.0 (2024 R2).")

    TEST_DATA_ROOT_DIR = pathlib.Path(__file__).parent / "data" / "model_with_beams_shells_solids"
    model_name = "model_with_beams_shells_solids"
    files = ContinuousFiberCompositesFiles(
        rst=os.path.join(TEST_DATA_ROOT_DIR, f"{model_name}.rst"),
        composite={
            "shell": CompositeDefinitionFiles(
                definition=os.path.join(TEST_DATA_ROOT_DIR, f"{model_name}.h5"), mapping=None
            )
        },
        engineering_data=os.path.join(TEST_DATA_ROOT_DIR, f"{model_name}.engd"),
        files_are_local=True,
    )

    model = CompositeModel(files, server=dpf_server)

    # homogeneous solid
    solid = model.get_element_info(3)
    assert solid.is_layered == False
    assert all(solid.dpf_material_ids == np.array([1]))
    assert solid.n_layers == 1
    assert solid.n_spots == 0
    assert solid.element_type == 185

    # layered shell
    shell = model.get_element_info(34)
    assert shell.is_layered
    assert all(shell.dpf_material_ids == np.array([4, 4, 2, 4, 4]))
    assert shell.n_layers == 5
    assert shell.n_spots == 3
    assert shell.element_type == 181

    # beam
    beam = model.get_element_info(59)
    assert beam is None
