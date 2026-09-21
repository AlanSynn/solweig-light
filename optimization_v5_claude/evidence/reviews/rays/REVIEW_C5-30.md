# REVIEW C5-30 — R01a guarded absorption exit in `_trace_pixel`

- **Patch**: commit `b66fea64` on `perf/claude-glm53-cpu-v5-ray`, worktree `/Users/alansynn/Workspace/solweig-light-v5-ray` (base `bfd9915e`)
- **Reviewer**: independent GLM review (Opus unavailable). Not the author.
- **Date**: 2026-09-20
- **Verdict**: **ACCEPT**

## 1. Scope

`git diff bfd9915e..b66fea64 --name-only` touches exactly:

- `src/solweig_light/geometry/sky_compiled.py`
- `tests/optimization_v5/rays/test_r01a_absorption_exit.py` (new)

No other file. **No scope violation.** Worktree HEAD is `b66fea64` with a clean status, so the test runs below executed exactly the reviewed commit.

The source diff has exactly three hunks: module docstring (lines 17-21), the guarded exit + comment inside `_trace_pixel` (patched lines 303-312), and a comment update in `_shadow_pixel` (patched lines 343-348). A full-file `diff` of `bfd9915e:` vs `b66fea64:` versions confirms nothing else changed — `_maximum`, `_advance_pixel`, `_advance_*`, `_bush_*`, `_finish_*`, `_run_*`, `_shadow`, and `ray_schedule` are byte-identical to base. The `bush.max()>0` routing predicate in `_shadow_pixel` (patched line 339) is unchanged; only its trailing comment changed.

## 2. Proof verification (independent, from the code)

The patch inserts, as the last statement of the `for step` loop body:

```python
if step>0 and sh==np.float32(1):
    break
```

after the step's f/sh/vs updates, the `vs*sh>0 -> vs=0` reset, `vb+=vs`, and the `step==0` block. I verified each link of the guarded-exit argument from the actual code:

1. **f monotone, NaN-sticky.** `f=_maximum(f,building)` with `_maximum` returning `left` on `isnan(left)`, `right` on `isnan(right)` (base lines 74-79). For non-NaN operands `f_new>=f_old`; a NaN `building` turns `f` NaN; once NaN, `_maximum(NaN,·)` returns NaN forever. So f is nondecreasing on the reals and sticky-NaN on contamination.
2. **sh stays 1 after transition.** `if f>height: sh=1 elif f<=height: sh=0` (patched 287-290): with `f>height` and a later non-NaN sample, `max` keeps `f>height` -> `sh=1` again; with a NaN sample both comparisons are False -> sh **unchanged** (=1). NaN f is sticky, so sh can never revert to 0 after the transition. Absorption requires strict `f>height`: a sample exactly equal to the running max leaves `f==height` -> `sh=0` -> **no break**, as required.
3. **vs/vb frozen in the skipped suffix.** vs stays in {0.0, 1.0}: init `float32(bush>1)` ∈ {0,1}; the max operand `float32(veg>h)-float32(trunk>h)` ∈ {-1,0,+1} and `max(vs,-1)=vs`; no -0.0 in vs's value domain (0.0-0.0=+0.0, 1.0-1.0=+0.0). At the transition step the reset runs while `sh==1` (sh is updated before the reset), so any vs==1 becomes 0 **before** `vb+=vs`; hence vs==0.0 and vb unchanged at break time. By induction every original later step t: `vs=max(0,k)` then reset (sh==1) re-zeroes it, `vb+=0`. So the original's end-of-loop (sh,vs,vb) equals the break-time triple.
4. **`vb+=0` skip is bitwise-safe.** vb is +0.0 or positive in-loop (init `np.float32(0)`, step-0 block re-sets `+0.0`, only additions before the finish block), so `vb+0.0` is a bitwise no-op; skipping it cannot flip a sign bit.
5. **First step correctly excluded.** At step 0 the special block runs *after* the reset and can leave `vs=1` (with sh possibly 1) and `vb=0`. In the original, a later step's reset zeroes that vs **before** `vb+=vs`, and the finish block then computes `vb-vs` and `1-vs` from vs==0. A break at step 0 would strand vs==1 and change both outputs — the `step>0` guard is load-bearing, and it is present (patched line 311). Conversely the transition-step reset provably runs before the break (ordering: updates at 286-294, step-0 block 295-302, break check 311-312) — the exact case "step-0 sets vs=1, step 1 absorbs" is handled, and is pinned by `test_first_step_hit_must_not_break`.
6. **Finish block and outputs.** `if vb>0: vb=1; vb=vb-vs; if vs>0: vs=1; return 1-sh,1-vs,1-vb` (patched 313-316) reads only the frozen triple, so outputs are bit-identical, including NaN positions (there are none — sh/vs/vb are always exact {0,1} floats or {-1,0,1} for pre-clamp vb) and signed zeros (only +0.0 producible).
7. **Domain of the break.** Fires only when `sh==np.float32(1)` (exact float32 comparison; sh is never NaN) at `step>=1`. Empty schedules never enter the loop; one-step schedules never satisfy `step>0`; a break at the final step is equivalent to loop end. Every behavior outside the absorbing suffix executes the byte-identical original loop.

I found no input regime where the patch can change the returned masks. The only behavioral difference is skipped work inside a provably output-invariant suffix.

## 3. Test honesty

- **Reference is pristine.** Normalized diff (indentation stripped, `_maximum_reference` -> `_maximum`) of test lines 42-80 against `bfd9915e:src/solweig_light/geometry/sky_compiled.py` lines 265-302 shows the bodies are token-identical; the only differences are the decorator (`cache=False`, no `inline`) and the function name. `fastmath=False` on both. Not candidate-generated. The harness host prep (`_reference_pixel_trace`) mirrors `_shadow_pixel`'s no-bush branch line for line (dtype mapping a/canopy/trunk -> da/dv/dt is the vegdem/vegdem2 correspondence, correct).
- **Bitwise comparison.** `_bitwise` asserts float32 dtype, shape, `uint32`-view equality (covers payloads/signbits), plus an explicit NaN-position check (redundant but documented). Both serial and parallel pixel routes are compared. No weakened comparison anywhere.
- **Negative controls are real.** I reproduced both mutations in a /tmp scratch package against the committed suite:
  - break-at-first-step (`if sh==np.float32(1):`): **8 failed, 23 passed** — matches the author's claim.
  - break-before-updates (check hoisted above the vs update/reset/accumulation): **17 failed, 14 passed** — matches the author's claim.
  The unmutated scratch package passes 31/31 cold, so the mutations, not the harness, cause the failures. (Controls are out-of-band evidence, not encoded as permanent mutation tests — acceptable under the v5 protocol, noted in §5.)
- **Schedule-length anchors assert counts.** `test_schedule_length_anchors` asserts actual `len(ray_schedule(...))` values (0, 1, 2, 5, 17, 33, 160, 32), and the empty/one/two-step tests each assert the exact count before running (lines 137-139, 169, 179, 196, 211, 234, 246, 269). Not shape-only.
- **No skips/xfails.** No `skip`, `xfail`, or conditional bail in the file; `_run` hard-asserts the no-positive-bush harness precondition.
- **Coverage is genuinely adversarial:** first/second-step hits, late hit (17x33), early hit with 150+ step suffix (17x160), receiver below zero, zero-padding empty-window suffix, canopy/trunk gap patterns, signed zeros (-0.0 fields), NaN/Inf after absorption / on transition / at receivers, 12 seeded random configs incl. 160-step schedules, float64 scene, and a positive-bush fallback route-identity test against the untouched step-major entry (bitwise).

## 4. What I ran (observed numbers)

All runs by me, in the reviewed worktree, `NUMBA_NUM_THREADS=2`:

| Command | Result |
|---|---|
| `uv run pytest tests/optimization_v5/rays -q` | **31 passed** in 1.58s |
| `uv run pytest tests/differential/test_sky_compiled.py -q -k "not parallel4 and not parallel10 and not 4- and not 10-"` | **528 passed**, 608 deselected in 1.91s |
| Mutation A (first-step break), owned suite | **8 failed**, 23 passed |
| Mutation B (break-before-updates), owned suite | **17 failed**, 14 passed |
| Scratch unmutated control, owned suite | **31 passed** (cold cache) |

Notes on the oracle subset: `test_additional_edges_against_p1_numpy_diagnostic` uses raw int thread ids (`4-`, `10-`), so the lead's suggested `-k "not thread4 and not thread10"` does not apply; with only the `parallel4/parallel10` deselect, one edges test failed with `ValueError: The number of threads must be between 1 and 2` from `numba.set_num_threads(4)` under the thread cap — purely environmental, on the untouched `step` variant, not a patch failure. I verified the `4-`/`10-` substring deselect removes only edges-test thread variants plus already-deselected `parallel4-*` ids; no case coverage is lost. The oracle subset compares against the pristine upstream CPU oracle (`evidence_class original_upstream_cpu`, source `0d7fe742`) and includes the `pixel` variant and the `fractional_bush` fallback-routing case, so it independently corroborates the patch against a non-candidate oracle.

## 5. Issues found

- **[cosmetic] test_r01a_absorption_exit.py:116-117** — comment claims "NaN bush routes to the fallback", but `bush.max()` with NaN returns NaN and `NaN>0` is False, so a NaN bush would actually route to the pixel path. Unreachable in practice: `_run`'s `bush.max()<=0` assert rejects NaN bush before any run (NaN<=0 is False), so nothing is weakened. No code change required.
- **[informational] Negative controls are not encoded in the committed suite** — they are evidence claims in the commit message. I reproduced both exactly (8 and 17), so the claims stand; recording the mutation recipes here preserves reproducibility.
- **[informational] Break skips `vb+=vs` rather than executing it** — proven bitwise-safe because vb is never -0.0 in-loop (§2.4), but any future refactor that lets vb go negative before the finish block would invalidate this. The comment block at patched lines 303-310 documents the invariant; keep it in sync.

No blocking issues.

## 6. Limitations

- Route: GLM (Z.ai); Opus was unavailable, per the routing manifest. Review performed independently of the author from the diff and both file versions.
- Differential/oracle runs use the thread cap (`NUMBA_NUM_THREADS=2`); the 4/10-thread oracle variants were deselected as environmental (they cannot run under the cap). The owned suite's parallel route ran at 2 threads.
- The equivalence proof is analytic (§2) plus empirical (crafted + seeded differential); it is not an exhaustive formal proof over all float inputs. The NaN-stickiness and {0,1}-domain arguments cover the regimes I could construct, and the seeded random scenes with 160-step schedules exercise transitions densely.
