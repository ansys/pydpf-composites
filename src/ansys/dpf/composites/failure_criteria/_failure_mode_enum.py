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

from enum import Enum

# Use the functional API because otherwise it is impossible to use
# python keywords as enum values (such as "as")
# Note: This enum should to be in sync with the corresponding enum in dpf_composites.
FailureModeEnum = Enum(
    "FailureModeEnum",
    [
        # Strain failure criteria
        ("emax", 101),
        ("evm", 102),
        ("e1", 110),
        ("e1t", 111),
        ("e1c", 112),
        ("e2", 120),
        ("e2t", 121),
        ("e2c", 122),
        ("e3", 130),
        ("e3t", 131),
        ("e3c", 132),
        ("e12", 140),
        ("e13", 150),
        ("e23", 160),
        # Stress failure criteria
        ("smax", 201),
        ("svm", 202),
        ("s1", 210),
        ("s1t", 211),
        ("s1c", 212),
        ("s2", 220),
        ("s2t", 221),
        ("s2c", 222),
        ("s3", 230),
        ("s3t", 231),
        ("s3c", 232),
        ("s12", 240),
        ("s13", 250),
        ("s23", 260),
        # Sandwich failure criteria
        ("cf", 310),  # core shear
        ("w", 320),  # wrinkling
        ("wb", 321),  # wrinkling bot face sheet
        ("wt", 322),  # wrinkling top face sheet
        ("sc", 330),  # shear crimping
        # Classical failure criteria
        # from laminate theories
        ("tw", 400),  # tsai wu
        ("th", 500),  # tsai hill
        ("h", 501),  # hill
        ("hf", 601),  # hashin fiber
        ("hm", 602),  # hashin matrix
        ("hd", 603),  # hashin delamination
        ("ho", 700),  # hoffmann
        ("p", 800),  # puck
        ("pf", 801),  # puck fiber
        ("pmA", 802),  # puck matrix modus A
        ("pmB", 803),  # puck matrix modus B
        ("pmC", 804),  # puck matrix modus C
        ("pd", 805),  # puck 3D delamination
        ("l", 900),  # larc failure criterion
        ("lft3", 901),  # larc fiber failure tension LaRC  # 3
        ("lfc4", 902),  # larc fiber failure compression LaRC  # 4
        ("lfc6", 903),  # larc fiber failure compression LaRC  # 6
        ("lmt1", 904),  # larc matrix tension failure LaRC  # 1
        ("lmc2", 905),  # larc matrix compression failure LaRC  # 2
        ("lmc5", 906),  # larc matrix compression failure LaRC  # 5
        ("c", 1000),  # cuntze
        ("cft", 1001),  # cuntze fiber failure tension
        ("cfc", 1002),  # cuntze fiber failure compression
        ("cmA", 1003),  # cuntze matrix failure tension
        ("cmB", 1004),  # cuntze matrix failure compression
        ("cmC", 1005),  # cuntze wedge shape matrix failure
        ("vMe", 1101),  # elastic von mises strain failure
        ("vMs", 1102),  # elastic von mises stress failure
        ("as", 1201),  # adhesive shear stress failure
        ("ap", 1202),  # adhesive peel stress failure
        ("af", 1203),  # adhesive fracture stress failure
        # Allow to  mark text as ns = no show in order to not show
        # failure mode labels below / above a threshold etc.
        ("ns", 9998),
        # If no failure mode can be computed, explicitly assign n/a - not available.
        ("na", 9999),
    ],
)
