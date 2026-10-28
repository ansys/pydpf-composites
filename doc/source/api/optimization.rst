Laminate optimization
---------------------

.. module:: ansys.dpf.composites.optimization

See :doc:`../optimization` for symmetry semantics, load conventions, examples,
and PyACP write-back limitations.

.. autosummary::
    :toctree: _autosummary

    Material
    AnalysisPlyInfo
    LaminateForces
    LoadCase
    Laminate
    AngleBounds
    DiscreteAngles
    PlyRule
    AdditionRule
    DesignVariable
    LaminateDesignSpace
    LaminateResponse
    LaminateEvaluator
    ClassicalLaminateEvaluator
    PointResult
    CandidateEvaluation
    LaminateOptimizationProblem
    SpatialPlyExtentOptimizer
    LaminateOptimizationResult
    PlyChange
    LaminateChangeSet
    ACPAdditionTemplate
    ACPChange
    PyACPAdapter
    scipy_differential_evolution
    scipy_minimize
    InvalidDesign