"""Composite Scope."""
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class CompositeScope:
    """Provides the composite scope.

    This class defines which part of the model and solution step are selected.

    Parameters
    ----------
    elements:
        List of elements.
    plies:
        List of plies.
    time:
        Time or frequency. You can use the
        :meth:`.CompositeModel.get_result_times_or_frequencies` method
        to list the solution steps.
    named_selections:
        List of element sets.
        Use `composite_model.get_mesh().available_named_selections` to list
        all named selections.

    Notes
    -----
    If more than one scope (``elements``, ``named_selections`` and ``plies``)
    is set, then the final element scope is the intersection
    of the defined parameters. All elements are selected if no parameter is set.

    """

    elements: Optional[Sequence[int]] = None
    plies: Optional[Sequence[str]] = None
    time: Optional[float] = None
    named_selections: Optional[Sequence[str]] = None
