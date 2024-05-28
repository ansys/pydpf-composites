# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""Composite Model Interface."""
# New interface after 2023 R2
from collections.abc import Collection, Sequence
from typing import Any, Callable, Optional, cast
from warnings import warn

import ansys.dpf.core as dpf
from ansys.dpf.core import FieldsContainer, MeshedRegion, Operator, UnitSystem
from ansys.dpf.core.server_types import BaseServer
import numpy as np
from numpy.typing import NDArray

from .composite_scope import CompositeScope
from .constants import FAILURE_LABEL, REF_SURFACE_NAME, TIME_LABEL, FailureOutput
from .data_sources import (
    CompositeDataSources,
    ContinuousFiberCompositesFiles,
    get_composites_data_sources,
)
from .failure_criteria import CombinedFailureCriterion
from .layup_info import (
    ElementInfo,
    LayerProperty,
    LayupModelContextType,
    LayupPropertiesProvider,
    add_layup_info_to_mesh,
    get_element_info_provider,
)
from .layup_info._layup_info import _get_layup_model_context
from .layup_info._reference_surface import (
    _get_map_to_reference_surface_operator,
    _get_reference_surface_and_mapping_field,
)
from .layup_info.material_operators import MaterialOperators, get_material_operators
from .layup_info.material_properties import MaterialProperty, get_constant_property_dict
from .result_definition import FailureMeasureEnum
from .sampling_point import SamplingPointNew
from .server_helpers import (
    upload_continuous_fiber_composite_files_to_server,
    version_equal_or_later,
    version_older_than,
)
from .unit_system import get_unit_system


def _create_material_container_helper_op(material_provider: Operator) -> Operator:
    try:
        helper_op = dpf.Operator("composite::materials_container_helper")
    except Exception as exc:
        raise RuntimeError(
            f"Operator composite::materials_container_helper doesn't exist. "
            f"This could be because the server version is 2024 R1-pre0. The "
            f"latest preview or the unified installer can be used instead. "
            f"Error: {exc}"
        ) from exc
    helper_op.inputs.materials_container(material_provider.outputs)
    return helper_op


def _deprecated_composite_definition_label(func: Callable[..., Any]) -> Any:
    """Emit a warning when the deprecated ``composite_definition_label`` is used."""
    function_arg = "composite_definition_label"

    def inner(*args: Sequence[Any], **kwargs: Sequence[Any]) -> Any:
        if function_arg in kwargs.keys():
            if kwargs[function_arg]:
                warn(
                    f"Use of {function_arg} is deprecated. Function {func.__name__}."
                    " can be called without this argument.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
        return func(*args, **kwargs)

    return inner


def _merge_containers(
    non_ref_surface_container: FieldsContainer, ref_surface_container: FieldsContainer
) -> FieldsContainer:
    """
    Merge the results fields container.

    Merges the results fields container of the non-reference surface and the reference surface.
    """
    assert sorted(non_ref_surface_container.labels) == sorted(ref_surface_container.labels)

    ref_surface_time_ids = ref_surface_container.get_available_ids_for_label(TIME_LABEL)
    non_ref_surface_time_ids = non_ref_surface_container.get_available_ids_for_label(TIME_LABEL)

    assert sorted(ref_surface_time_ids) == sorted(non_ref_surface_time_ids)

    out_container = dpf.FieldsContainer()
    out_container.labels = [TIME_LABEL, FAILURE_LABEL]
    out_container.time_freq_support = non_ref_surface_container.time_freq_support

    def add_to_output_container(time_id: int, source_container: FieldsContainer) -> None:
        fields = source_container.get_fields({TIME_LABEL: time_id})
        for field in fields:
            failure_enum = _get_failure_enum_from_name(field.name)
            out_container.add_field({TIME_LABEL: time_id, FAILURE_LABEL: failure_enum}, field)

    for current_time_id in ref_surface_time_ids:
        add_to_output_container(current_time_id, ref_surface_container)
        add_to_output_container(current_time_id, non_ref_surface_container)

    return out_container


def _get_failure_enum_from_name(name: str) -> FailureOutput:
    if name.startswith("Failure Mode"):
        if name.endswith(REF_SURFACE_NAME):
            return FailureOutput.FAILURE_MODE_REF_SURFACE
        else:
            return FailureOutput.FAILURE_MODE

    if name.startswith("IRF") or name.startswith("SF") or name.startswith("SM"):
        if name.endswith(REF_SURFACE_NAME):
            return FailureOutput.FAILURE_VALUE_REF_SURFACE
        else:
            return FailureOutput.FAILURE_VALUE

    if name.startswith("Layer Index"):
        return FailureOutput.MAX_LAYER_INDEX

    if name.startswith("Global Layer in Stack"):
        return FailureOutput.MAX_GLOBAL_LAYER_IN_STACK

    if name.startswith("Local Layer in Element"):
        return FailureOutput.MAX_LOCAL_LAYER_IN_ELEMENT

    if name.startswith("Solid Element Id"):
        return FailureOutput.MAX_SOLID_ELEMENT_ID

    raise RuntimeError("Could not determine failure output from name: " + name)
