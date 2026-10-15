# Follow-on end-to-end headroom review

This bundle is a diagnosis artifact, **not a completed optimization campaign**.
It accepts the user's verified S10 records. It does not remeasure or change S10.

Read:
1. `DIAGNOSIS.md`: conditional floors, envelope limits and candidate priorities.
2. `PHASE0_HANDOFF.md`: M1–M6 specification and conditional implementation gates.
3. `PHASE0_PROTOCOL.template.json`: bind to real local code, fixtures and allocation
   before timing. Null fields are intentional; no guessed API is supplied.
4. `FOLLOWON_STATUS.json`: honest completion and access boundaries.

Reproduce the local arithmetic and counterexample:

```sh
python tools/floor_model.py --output /tmp/solweig-floor-arithmetic.json
python tools/guard_counterexample.py --output /tmp/solweig-guard-counterexample.json
python -m unittest discover -s tests -v
```

Only Python's standard library is required. These commands do not import SOLWEIG,
change a repository, submit jobs, download dependencies or produce host speedups.
The numerical values in `evidence/floor_arithmetic.json` are derived or hypothetical;
none are new Slurm measurements. The metadata counterexample is an executed local
correctness example, not a test of the unseen c245ea60 implementation.

The target workspace is unavailable to this session. The remote GitHub connection
exposes only main; c245ea60 and the S10 branch cannot be fetched. No native/source
patch was made and no independent subagent review took place. Implementation must
wait for the prescribed actual attribution and safe branch creation on the host.

## External primary references used

- Numba threading layer, masks, runtime/process interaction:
  https://numba.readthedocs.io/en/stable/user/threading-layer.html
- Slurm CPU allocation and binding:
  https://slurm.schedmd.com/srun.html
  https://slurm.schedmd.com/cpu_management.html
- Python profiling is not benchmark timing:
  https://docs.python.org/3.11/library/profile.html
- CPython BytesIO backing-buffer behavior (example interpreter lineage, inspect the deployed version):
  https://raw.githubusercontent.com/python/cpython/3.11/Modules/_io/bytesio.c
- Array equality is not byte identity:
  https://numpy.org/doc/stable/reference/generated/numpy.array_equal.html

The supplied performance records were not downloaded here. Their exact protocol,
fixture and environment hashes remain a local binding prerequisite.
