# M7 — Integration recipe for the private phase memory admission (C6-42)

Status: **proposed recipe for the integrator; nothing here is applied.**  The
module `src/solweig_light/runtime_memory.py` is inert at base `5e1fab46`
(nothing in `src` imports it; asserted by
`tests/optimization_v6/memory/test_phase_memory_admission.py::test_module_is_inert_until_wired`).
`runtime.py`, `api.py`, and `geometry/service.py` are integrator-owned
(dossiers/09 shared-file authority); this directory only carries the diff
proposal `m7_phase_admission_wiring.proposed.patch`.

Revision notes (2026-09-21): (1) module/tests updated for the C6-60 review
corrections — walls/aspects are float32 tile residents; 3×1 added as an
explicit raw-worst breach configuration alongside 4×1 (raw-safe worker count
at 12 GiB is 2).  (2) C6-42 review fixes: the proposed patch was regenerated
with `git diff` (the hand-written copy was malformed and failed
`git apply --check`); the patch now forwards `block_pixels` to
`shape_from_building_dsm` at W1/W2; `plan_phase_admission` validates that
preprocess jobs use the default `visibility_mode`/`export_overlap` and
forwards both for geometry/simulation; the §3 sign-off interval and the
width-3 statement are corrected; parent-side GDAL caching safety is
documented in §1; the gate test count is updated.

## 1. Wiring points (three, all parent-side)

| # | File:anchor | Change | Semantics preserved |
|---|---|---|---|
| W1 | `api.py` `run_utci_tiles`, immediately after the existing `plan_admission(jobs, runtime)` (api.py:157) | Add `plan_phase_admission(..., policy='reject')` over `PhaseJob` descriptors built with `shape_from_building_dsm` | Rejection raises `ResourceAdmissionError` in the parent **before any worker exists** — the m3 §3 resource-failure column is unchanged (admission failure aborts; no child has started, so "remaining jobs never start" holds a fortiori) |
| W2 | `geometry/service.py` `prepare_geometry_exports`, immediately after the existing `plan_admission(...)` (service.py:275) | Add a single-job geometry-phase check, `policy='reject'`, `active_workers=1` | Same in-process failure point as today; the comment at service.py:272-274 ("opens only DSM metadata") stays true — `shape_from_building_dsm` opens metadata only |
| W3 | `runtime.py` `_child_environment` (runtime.py:663-676) | Set `GDAL_CACHEMAX` (MB) to the per-worker allowance charged by the calculator | Converts the largest M2 §6a miss from a pure reservation into an enforced cap; children read the env at GDAL first use, before any numerical import, matching the existing thread-cap mechanism |

Policy choice for public wiring is **reject**, matching today's public
semantics (`ResourceAdmissionError` aborts — m3 §3).  The `queue` policy is
for the future v6 phase adapter only; it must not be enabled in public
wiring without its own design review, because queueing changes observable
scheduling behavior.

Parent-side GDAL caching (M2 §6a, second half): the calculator charges the
GDAL block cache **per worker child** (W3 enforces it), but the parent
process also accumulates GDAL block-cache bytes while it runs.  This is
currently safe to leave unmodeled in the parent footprint for three
reasons, all verified at base `5e1fab46`: (a) every parent-side GDAL open
is a metadata-only schema probe — `shape_from_building_dsm` mirrors
service.py:272-274 ("opens only DSM metadata"), and the export schema probe
writes/reads a 1×1 template in a temporary directory that is deleted before
return (service.py:86-104); (b) parent raster datasets are closed before
dispatch (the `dataset = None` idiom at service.py:69-70, 96-99, 132-133),
and GDAL's block cache only holds bytes for **open** datasets' touched
blocks, so per-tile datasets do not accumulate across the run; (c) the
parent performs no raster block IO at all — all ReadAsArray work happens in
children, whose caches W3 caps.  Residual exposure: the parent's
`default_gdal_cache_bytes()` allowance (5% of physical RAM) is an upper
bound only if a future change keeps a parent-side dataset open across
worker dispatch; if that happens, the parent footprint constant
(`DEFAULT_PARENT_FOOTPRINT_BYTES`) must be revisited in the same patch.

## 2. Failure-semantics contract (C6-03 m3, binding on the integrator)

1. The calculator raises the **existing** `runtime.ResourceAdmissionError`
   (re-exported by `runtime_memory`).  Do not pickle it and do not raise it
   from a worker: admission decisions run in the parent before dispatch.
   If a worker ever re-checks admission, its failure must surface through
   the existing `_child_exception` rebuild (m3 §7.4), never plain pickling.
2. Missing shape data raises (`shape_from_building_dsm` on an unreadable
   Building_DSM, malformed `PhaseJob` dimensions).  There is no code path
   that treats unknown shape as a zero-byte reservation.
3. No `np.seterr` manipulation anywhere in the calculator; arithmetic is
   pure Python integers with no negative intermediates (a budget exhausted
   by parent/writer-queue overhead raises before reservations are summed).
4. The first serial-order failure rule (m3 §7.3) is untouched: admission
   happens before dispatch, so a rejection cannot remove lower-index
   completed artifacts or reorder publication.

## 3. Deliberate boundary change to sign off (integration decision)

The corrected single-job geometry reservation (4,758,857,318 B at
1024/P153/block1024, raw fallback) **exceeds** the legacy estimate
(3,730,374,656 B).  With W2, budgets in the interval
**[3.4742, 4.8320) GiB** would newly raise `ResourceAdmissionError` for a
cold worst-case geometry job that today is admitted: the lower bound is the
legacy single-job estimate (3,730,374,656 B — the legacy `plan_admission`
check charges **no parent term**), and the upper bound is the corrected
model's admit threshold for the same job including the parent footprint
(0.4 GiB parent + 4,758,857,318 B reservation ≈ 4.8320 GiB).  This is the
corrected-boundary behavior the C6-42 gate asks for (the legacy model
under-admits cold geometry), but it is a **stricter public admission
boundary** and needs the integrator's explicit sign-off, or W2 can be
deferred to the phase-adapter patch where the boundary change lands together
with parallel geometry.

At the 12 GiB budget the two models agree at width 2×2 (both admit).  They
disagree at width 3×1: the legacy model admits (3 × 3.4742 GiB ≤ 12 GiB)
while the corrected model narrows the request to 2 active workers, because
3 × 5,741,962,854 B raw-worst reservations + parent exceed the budget.  That
narrowing is the intended C6-60 F6 correction, not a regression; W1 does
change behavior for width-3 requests and that is the point.

## 4. Ordering and barriers

- W1 runs before `execute_tiles` (simulation dispatch) — after the
  all-geometry-complete barrier (m3 §4), unchanged.
- W2 runs inside `prepare_geometry_exports`, before any raster work.
- The future parallel-geometry adapter must call `plan_phase_admission`
  with `policy='queue'` per geometry wave and keep `admissible_workers`
  as its concurrency bound; the all-geometry barrier still applies before
  any simulation admission.

## 5. Integrator acceptance gates

1. `PYTHONPATH=src .venv-light/bin/python -m pytest tests/optimization_v6/memory/ -q` — all pass (31 at base 5e1fab46+module, rev 3).
2. Affected small interaction (L2, VALIDATION_POLICY): one 64/128-square
   TIFF-to-TIFF run with `memory_budget_bytes` set inside and outside the
   corrected boundary; verify `ResourceAdmissionError` aborts before worker
   spawn and nothing is published on rejection.
3. Confirm `RuntimeOptions.as_dict()`, the seven public signatures, and
   `runtime.__all__` are unchanged (D04/D09).
