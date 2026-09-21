#!/usr/bin/env python3
"""C5-62 parity verification: candidate large-run outputs vs frozen v4 reference.

Compares every recorded output sha256/size in a v5 candidate_manifest.json
against the reused v4 large_runs_v1 reference manifest for the same case.
Usage: verify_parity.py <candidate_manifest.json> <case>
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REF_ROOT = Path("/Users/alansynn/Workspace/solweig-light/reports/characterization/"
                "local_cpu_optimization_v1/qualification/final_combined_v1/large_harness/large_runs_v1")


def main() -> int:
    cand_path = Path(sys.argv[1])
    case = sys.argv[2]
    cand = json.loads(cand_path.read_text())
    ref = json.loads((REF_ROOT / case / "candidate_manifest.json").read_text())

    if cand["fixture_manifest_sha256"] != ref["fixture_manifest_sha256"]:
        print("FAIL fixture manifest sha256 differs")
        return 1
    if cand["profile"]["fingerprint"] != ref["profile"]["fingerprint"]:
        print("FAIL math profile fingerprint differs")
        return 1
    ref_ro = dict(ref["runtime_options"]); cand_ro = dict(cand["runtime_options"])
    if ref_ro != cand_ro:
        print("FAIL runtime_options differ")
        print(" ref:", json.dumps(ref_ro, sort_keys=True))
        print(" cand:", json.dumps(cand_ro, sort_keys=True))
        return 1

    ref_map = {o["path"]: (o["bytes"], o["sha256"]) for o in ref["outputs"]}
    cand_map = {o["path"]: (o["bytes"], o["sha256"]) for o in cand["outputs"]}
    if set(ref_map) != set(cand_map):
        print("FAIL output path sets differ")
        print(" ref-only:", sorted(set(ref_map) - set(cand_map)))
        print(" cand-only:", sorted(set(cand_map) - set(ref_map)))
        return 1
    diffs = [p for p in sorted(ref_map) if ref_map[p] != cand_map[p]]
    if diffs:
        for p in diffs:
            print(f"FAIL {p}: ref {ref_map[p]} != cand {cand_map[p]}")
        return 1
    print(json.dumps({"case": case, "outputs": len(cand_map),
                      "parity": "BITWISE_PASS",
                      "ref_elapsed_diagnostic_seconds": ref["elapsed_diagnostic_seconds"],
                      "cand_elapsed_diagnostic_seconds": cand["elapsed_diagnostic_seconds"],
                      "ratio": round(ref["elapsed_diagnostic_seconds"] / cand["elapsed_diagnostic_seconds"], 4)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
