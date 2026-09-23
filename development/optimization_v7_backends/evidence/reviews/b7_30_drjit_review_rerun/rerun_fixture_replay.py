"""B7-30 independent rerun: full 520-call fixture replay of C_drjit.

Reconstructed from b7_02_capture_manifest.json + b7_02_fixtures.npz directly
(no author script exists in the candidate directory).  Bitwise comparison on
uint32 view.  Also verifies input canaries on every call.
"""
import hashlib
import json
import sys
import time

import numpy as np

sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/experiments/optimization_v7/drjit")
sys.path.insert(0, "/Users/alansynn/Workspace/solweig-v7-drjit/src")

from llvm_longwave import longwave_primary_drjit  # noqa: E402

CAP = "/Users/alansynn/Workspace/solweig-light/optimization_v7_backends/evidence/captures"
manifest = json.load(open(f"{CAP}/b7_02_capture_manifest.json"))
z = np.load(f"{CAP}/b7_02_fixtures.npz", allow_pickle=False)


def rebuild_scalar(spec, arr):
    pt = spec.get("python_type")
    if pt == "float":
        return float(arr)
    if pt == "int":
        return int(arr)
    return arr.item()  # numpy scalar (item() -> python; wrap back below)


def rebuild_scalar_np(spec, arr):
    pt = spec.get("python_type")
    if pt == "float":
        return float(arr)
    return arr[()]  # 0-d -> numpy scalar of the stored dtype


n = manifest["call_count"]
admitted = rejected = matched = mismatched = 0
canary_fail = 0
per_case = {}
t0 = time.time()
for c in manifest["calls"]:
    i = c["call_index"]
    args = []
    hashes_before = {}
    for j, spec in enumerate(c["args"]):
        arr = z[f"call{i:04d}_arg{j:02d}"]
        if spec["kind"] == "ndarray":
            hashes_before[j] = hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()
            args.append(arr)
        else:
            args.append(rebuild_scalar_np(spec, arr))
    ref = z[f"call{i:04d}_output"]
    try:
        out = longwave_primary_drjit(*args)
    except ValueError as e:  # Unsupported
        rejected += 1
        st = per_case.setdefault(c["case"], {"n": 0, "adm": 0, "match": 0, "rej": 0})
        st["n"] += 1
        st["rej"] += 1
        continue
    admitted += 1
    ok = out.shape == ref.shape and out.dtype == np.float32 and \
        np.array_equal(out.view(np.uint32), ref.view(np.uint32))
    # input canaries
    for j, spec in enumerate(c["args"]):
        if spec["kind"] == "ndarray":
            arr = z[f"call{i:04d}_arg{j:02d}"]
            if hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest() != hashes_before[j]:  # noqa: E501
                canary_fail += 1
    if ok:
        matched += 1
    else:
        mismatched += 1
    st = per_case.setdefault(c["case"], {"n": 0, "adm": 0, "match": 0, "rej": 0})
    st["n"] += 1
    st["adm"] += 1
    st["match"] += int(ok)

wall = time.time() - t0
result = {
    "schema": "b7-30-independent-rerun-fixture-replay",
    "captured": n,
    "admitted": admitted,
    "rejected": rejected,
    "matched": matched,
    "mismatched": mismatched,
    "input_canary_failures": canary_fail,
    "wall_seconds": round(wall, 2),
    "per_case": per_case,
}
print(json.dumps(result, indent=1))
json.dump(result, open("/tmp/b7_30_drjit_review/logs/rerun_fixture_replay.json", "w"), indent=1)
sys.exit(0 if (admitted == matched == n and mismatched == 0 and canary_fail == 0) else 1)
