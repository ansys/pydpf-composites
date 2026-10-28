Laminate optimization
=====================

The :mod:`ansys.dpf.composites.optimization` package optimizes complete local
laminates under fixed laminate force and moment resultants. A single shared
design is evaluated at all supplied sampling points and load cases. The default
objective is weighted mean mass per unit area; each point and load case must
satisfy its inverse reserve factor (IRF) limit.

Requirements and scope
----------------------

* The loaded DPF Composites plugin must provide
  ``composite::classical_laminate_theory_operator``. Availability is a plugin
  capability, not something inferred from the DPF server version.
* Sampling-point import additionally requires exported material definitions.
  Older sampling-point JSON is rejected explicitly. Alternatively, construct
  :class:`~ansys.dpf.composites.optimization.Laminate` objects from known data.
* The current standalone CLT schema supports shell laminates. All points,
  resultants, material properties, thicknesses and densities must use one
  consistent unit system. No implicit unit or coordinate conversion is made.
* Candidate material external IDs must exist in the evaluator's materials
  container, including materials not used in the initial layup. Density and
  failure allowables are read from that container, not from the JSON material
  definition. Variable properties use the backend's default material state.
* SciPy is optional. Install the ``optimization`` extra to use the supplied
  SciPy drivers. Custom optimizer and evaluator callables need no SciPy.

.. warning::

   These are **fixed-resultant, in-plane CLT feasibility** results for the
   supplied points and cases. They do not establish FE-level structural
   feasibility. Changed global stiffness can redistribute loads. Buckling,
   out-of-plane failures, strong stress gradients, and draping changes need
   separate verification. Apply a selected design in ACP and rerun the FE
   analysis before accepting it. Large changes may require an outer loop that
   refreshes the supplied resultants.

Build the optimization problem
------------------------------

The following illustrates a workflow with an existing ``composite_model`` and
a sequence of ``sampling_points`` from the same ACP model. Their complete
initial local stacks must already be symmetric for ``symmetric=True``.

.. code-block:: python

   from ansys.dpf.composites.failure_criteria import (
       CombinedFailureCriterion,
       MaxStressCriterion,
   )
   from ansys.dpf.composites.optimization import (
       DiscreteAngles,
       ClassicalLaminateEvaluator,
       Laminate,
       LaminateDesignSpace,
       LaminateOptimizationProblem,
       PlyRule,
       scipy_differential_evolution,
   )

   laminates = [
       Laminate.from_sampling_point(point, name=f"point_{i}")
       for i, point in enumerate(sampling_points)
   ]
   design_space = LaminateDesignSpace(
       laminates,
       default_rule=PlyRule(
           angles=DiscreteAngles((0, 15, 30, 45, 60, 75, 90)),
           removable=True,
       ),
       symmetric=True,
       minimum_plies=4,
   )
   criterion = CombinedFailureCriterion(
       failure_criteria=[MaxStressCriterion(s3=False, s13=False, s23=False)]
   )
   evaluator = ClassicalLaminateEvaluator(
       composite_model.material_operators.material_provider,
       criterion,
   )
   problem = LaminateOptimizationProblem(design_space, evaluator, irf_limit=0.9)
   result = problem.optimize(
       scipy_differential_evolution,
       seed=42,
       maxiter=100,
       popsize=10,
       polish=False,
   )
   if result.feasible:
       report = result.to_dict()
       changes = result.changes

The criterion above is suitable for regular/woven fiber plies. For sandwich or
other material types, supply appropriate supported criteria. The evaluator
rejects an uncovered ply type instead of treating a zero failure result as a
safety check. It also rejects out-of-plane max-stress/max-strain components and
3D criteria. A DPF ``LicenseContextManager`` for ``acpreppost`` can be held around
the run to avoid repeated license checkout overhead.

Shared identities and local variations
-------------------------------------

``design_space.global_ply_ids`` is the union of input analysis-ply IDs in
canonical order; ``common_ply_ids`` is still available for the intersection.
Edit rules can target any global ID and apply to every local occurrence of that
ply. Non-common plies remain in stacks where they occur and continue to
contribute stiffness, mass and failure constraints. Qualify ply IDs yourself
when combining different ACP models or composite definitions; names alone are
not globally unique. Each sampling-point name must also be unique.

Both ``AnalysisPlyInfo.id`` and the source ``AnalysisPlyInfo.global_ply_number`` are retained on import
and through angle/material edits, removals, reordering, CLT JSON export, and
change-set export. Global numbers are not replaced by local stack indices;
sparse numbers and large integers remain exact. Shared occurrences of the same
analysis-ply ID must not specify conflicting source global numbers.

The final ``plies`` tuple defines the candidate order. A preserved source global
number identifies the original ACP/DPF ply; it is not automatically changed into
the candidate's new manufacturing rank. Reordering in ACP can change global
numbers, so retain analysis-ply ID bindings and use the explicit ``global_order``
mapping when applying the new order. Do not use a mutable rank as the sole
cross-model identifier.

Added plies receive deterministic provisional global numbers above all supplied
source numbers. Each addition (including its mirrored partner) has a distinct
number shared across points and stable across candidate evaluations. These are
reserved only within the optimization inputs: final ACP numbers still require
checking unsampled model plies. Manually constructed plies may leave their
number as None; CLT serialization then supplies a temporary non-colliding schema
number without inventing an ACP source identity.

``ply_rules`` overrides ``default_rule`` for individual IDs. A rule's
``materials`` tuple is its fixed replacement group, expressed as material names.
It must include the initial material and all alternatives must have catalog
definitions. Supply additional :class:`~ansys.dpf.composites.optimization.Material`
objects using the design space's ``materials`` argument. Default replacement
preserves each local thickness; ``use_material_thickness=True`` instead uses
the catalog's ``nominal_thickness`` for the selected manufacturing product.
The initial product thickness must then match the initial local ply thickness.

Use ``AngleBounds(lower, upper)`` for continuous angles. Absolute angles assign
one local angle to all occurrences and require consistent initial local angles.
For differing rosette orientations, ``PlyRule(..., angle_mode="offset")`` applies
the same angle change to the existing local angle at every point. Its domain is
then a domain of **angle changes** and must include zero. Arbitrary draping
changes are not predicted. If a discrete angle domain does not contain an
initial angle, the initial numerical seed is projected to the nearest allowed
angle modulo 180 degrees (ties use the closest unwrapped value). The source
laminate is not mutated, and all decoded candidates use only the configured
allowed values. Continuous bounds still require the initial value to be in range.

Angles and order alone cannot reduce mass at fixed materials and thicknesses.
They can improve feasibility, allowing subsequent material substitution or ply
removal. Optionally pass an alternative objective callable to optimize failure,
stiffness, cost, or design-change penalties.

Symmetry
--------

``symmetric=True`` means reflection about the laminate's geometric mid-plane:
each reflected pair has the same material, thickness and fiber direction
(modulo 180 degrees). Symmetry is **not** +/- angle balance.

* Complete initial local stacks, including fixed patches, must be symmetric.
  This first implementation preserves symmetry rather than repairing an
  asymmetric initial layup.
* Mirror partners share angle, material and existence variables. Rules for
  both partners must be present and identical. A fixed counterpart cannot be
  silently changed to accommodate an editable ply.
* An existing odd center ply is independent and can remain or be removed.
* Each optional addition slot creates a mirrored pair; removing a reflected
  pair removes both members everywhere.
* Reordering permutes mirrored pairs and retains the center ply at the center.
* Every decoded **complete local laminate** is checked again for symmetry.

The symmetry plane need not be the FE reference plane. ``offset_policy`` is
``"midplane"`` by default, preserving the original mid-plane position as total
thickness changes. ``"bottom"`` preserves the bottom-surface position instead.
Resultant moments are always about the unchanged z=0 reference plane; no
reference-plane change is implied by editing the laminate geometry.

Topology changes
----------------

Use :class:`~ansys.dpf.composites.optimization.AdditionRule` for bounded optional
new plies. Each rule specifies its materials, thickness, angle domain, maximum
slot count. ``LaminateDesignSpace`` builds ``global_ply_ids`` as the canonical
ply order, using preserved source global ply numbers when available. It then
creates an integer ``position`` variable for each optional slot. The optimizer
chooses the insertion gap; the user does not name an ``after`` ply. Without
symmetry, each active slot adds one ply; with symmetry, each adds a pair. The
same added IDs and positions are projected into every local stack, skipping
global plies that are not present at that point. Inactive slots are omitted
from the DPF layup, never represented by zero thickness.

For example, ``position=2`` inserts before the third entry of the global ply
order. At a local stack containing only the first, second, and fourth global
plies, this projects to the gap before that local stack's fourth ply. If an
earlier ply is removed or common plies are reordered, the insertion is projected
through the surviving candidate order. In symmetric problems, only gaps in the
lower half are offered; the mirror gap is calculated automatically. The center
gap in an even-ply laminate yields a pair straddling the symmetry plane. If no
source IDs are common, additions-only problems still work: the global list is
formed from the union of the local stacks.

``allow_reordering=True`` enables random-key permutation variables. This first
implementation requires identical complete ply-ID sequences at all points;
reordering is rejected for different local stacks rather than guessing how to
move plies past fixed local patches. Addition positions follow the candidate
global order when reordering is enabled.

Connectivity-constrained local extents
---------------------------------------

To optimize where a global ply is present, pass a
:class:`~ansys.dpf.composites.optimization.SpatialPlyExtentOptimizer` as
``extent_optimizer`` to ``LaminateOptimizationProblem``. It takes an undirected
element adjacency mapping supplied by the caller. For shells, use elements
sharing an edge (not merely a node or diagonal contact). The graph keys must
cover exactly the sampling-point element IDs; optional positive
``element_weights`` should be element areas when minimizing physical mass.

The inner optimizer starts with each sampling point's existing ply mask. It
greedily tests removing one ply from one element, re-evaluating all configured
load cases and user constraints. A move is accepted only if it preserves
feasibility and decreases weighted mass. Every original connected component of
a ply's presence mask may shrink to empty or remain connected; a move that
splits it into islands is rejected. This prevents detached/checkerboard islands
under the supplied edge-sharing graph. It does not extend plies onto elements
where they were initially absent.

The inner search is deterministic and greedy, not an exact solution of the
joint binary-mask problem. ``max_evaluations`` bounds work per global candidate;
check ``result.best.extent_search_complete`` and
``result.best.extent_removals`` to see whether it exhausted all single-element
removals and what it removed. The global outer optimizer still controls shared
ply angle/material/design variables; the inner optimizer selects local extents
for each such candidate.

.. code-block:: python

   from ansys.dpf.composites.optimization import SpatialPlyExtentOptimizer

   extent_optimizer = SpatialPlyExtentOptimizer(
     element_neighbors,  # undirected edge-adjacency supplied by the caller
     element_weights=element_areas,
     max_evaluations=5000,
   )
   problem = LaminateOptimizationProblem(
     design_space,
     evaluator,
     irf_limit=0.8,
     extent_optimizer=extent_optimizer,
   )

Loads, constraints and algorithms
--------------------------------

Pass ``load_cases`` to ``Laminate.from_sampling_point`` to replace its extracted
initial resultants. Each point has its own sequence of named ``LoadCase``
objects with ``LaminateForces(Nx, Ny, Nxy, Mx, My, Mxy)``. There is no implicit
broadcast across points and no new FE solve during the inner optimization.
Resultants must already be in the local CLT frame with consistent signs and
units. Different cases can govern at different points.

An ``irf_limit`` mapping can specify a separate limit for every
``(point_name, case_name)`` pair. Each case contributes one constraint:
maximum ply IRF minus its limit must be <= 0. This vector stays fixed in size
as ply counts change. Additional scalar constraint callables take
``(laminates, point_results)`` and also use the <= 0 convention. Detailed results
retain the governing ply IRFs and failure modes, and the backend stress/strain
document is accessible through ``LaminateResponse.details``.

Mass is counted once per point, not once per load case. The objective uses
``Laminate.weight`` as a positive weight and divides by the sum of weights.
Equal weights are sampling weights; use representative areas when interpreting
mass savings over a region. The result is not automatically total model mass.

The optimizer interface is ``optimizer(problem, **options)``. It receives
``problem.design_space.initial``, ``bounds``, ``integrality``, ``objective(x)``
and ``constraint_values(x)`` and returns an object or dictionary with ``x``,
``success`` and ``message``. Objective and constraint requests share a cache.
Backend errors propagate; structurally invalid candidates are marked infeasible.

``scipy_differential_evolution`` supports the mixed variables. ``scipy_minimize``
supports continuous angles with fixed topology and defaults to SLSQP. It rejects
integer choices and permutation variables instead of rounding them. Solver
options, including iteration budgets and callbacks, are passed to SciPy.
Built-in DPF execution is serial; use a custom driver and isolated server
contexts for parallel evaluation. Do not pickle live DPF operators into SciPy
multiprocessing workers.

The best feasible evaluated candidate is retained independently of the solver's
termination flag and re-evaluated without cache before returning. Check
``result.feasible`` separately from ``result.solver_success``. If no evaluated
candidate is feasible, the result contains a least-violating valid fallback and
must not be applied as an accepted design. No global optimality is guaranteed.

Apply changes in PyACP
----------------------

``result.changes`` contains original/final local stack snapshots and ID-based
edits, additions and removals. Final snapshots also record reordering even if no
ply properties changed. ``result.to_dict()`` exports a JSON-serializable report.
A custom PyACP workflow can consume this change set without importing SciPy.

:class:`~ansys.dpf.composites.optimization.PyACPAdapter` provides conservative
write-back for one-to-one modeling-ply/analysis-ply relationships. Construct it
before optimization with explicit analysis-ply-ID -> ModelingPly bindings and
material-name -> Fabric mappings. AnalysisPly itself is read-only. The adapter
does not edit shared fabric definitions or infer material replacements by
similar names. Repeated layers, stackups, sublaminates, and variable-thickness
definitions need a custom adapter or explicit splitting first.

``adapter.apply(result)`` preflights and returns a dry-run plan. Real application
requires ``dry_run=False`` and a feasible result. Save a backup first: there is
no atomic transaction or automatic rollback. Local angle changes must correspond
to one common ACP design-angle change. Substitution fabrics must have the
optimized thickness. Removal deactivates the modeling ply rather than deleting
it, and one model update is performed after the operations.

Each added ply ID needs an ``ACPAdditionTemplate`` describing a modeling ply to
clone for its manufacturing extent and reference orientation. The extent
cannot be reconstructed from a few sampling points. Additions and reordering
also need explicit final ``global_order`` numbers covering every final local
ply, chosen to avoid collisions with unsampled plies. The adapter checks these
numbers against all final local stack orders. Generated additions are returned
in ``adapter.bindings`` under their optimization IDs.

The adapter does not change ACP offset definitions. Results with changed
offsets require ``offsets_verified=True`` only after the caller has arranged
matching ACP behavior. Re-export/regenerate local layups after applying changes
and verify material, angle, thickness, offset, order, and added ply coverage.
Then perform the final FE verification, including unsampled regions affected by
the shared manufacturing edits.