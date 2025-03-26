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

"""Utilities for managing the DPF server.

Helper functions for managing the DPF server, in particular for loading
the DPF Composites plugin.
"""

from ._connect_to_or_start_server import connect_to_or_start_server
from ._load_plugin import load_composites_plugin
from ._upload_files_to_server import (
    upload_continuous_fiber_composite_files_to_server,
    upload_file_to_unique_tmp_folder,
    upload_files_to_unique_tmp_folder,
    upload_short_fiber_composite_files_to_server,
)
from ._versions import version_equal_or_later, version_older_than

__all__ = (
    "load_composites_plugin",
    "connect_to_or_start_server",
    "upload_short_fiber_composite_files_to_server",
    "upload_file_to_unique_tmp_folder",
    "upload_files_to_unique_tmp_folder",
    "upload_continuous_fiber_composite_files_to_server",
    "version_older_than",
    "version_equal_or_later",
)
