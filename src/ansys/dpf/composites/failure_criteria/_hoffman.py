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

"""Hoffman failure criterion."""

from ._quadratic_failure_criterion import _DOC_DIM, _DOC_WF, QuadraticFailureCriterion


class HoffmanCriterion(QuadraticFailureCriterion):
    """Hoffman Criterion."""

    __doc__ = f"""Defines the Hoffman failure criterion for orthotropic reinforced materials.

    Parameters
    ----------
    wf:
        {_DOC_WF}
    dim:
        {_DOC_DIM}
    """

    def __init__(self, *, active: bool = True, wf: float = 1.0, dim: int = 2):
        """Create a Hoffman failure criterion for orthotropic reinforced materials."""
        super().__init__(name="Hoffman", active=active, dim=dim, wf=wf)
