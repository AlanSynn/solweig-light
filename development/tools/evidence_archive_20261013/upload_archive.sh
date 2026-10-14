#!/bin/bash
# Upload the solweig-light external evidence archive to Dropbox. Sequential with
# bounded retries; every put is logged with its exit status.
set -u
STAGE=/storage/scratch1/1/dsynn6/solweig-light-archive-staging
R="Alan Synn/Research/solweig-light"
LOG="$STAGE/logs/upload.log"
: > "$LOG"

put() { # put <local-abs-path> <remote-abs-path>
    local src="$1" dst="$2" attempt rc
    for attempt in 1 2 3; do
        if dbxcli put "$src" "$dst" >>"$LOG" 2>&1; then
            echo "OK   $dst"
            return 0
        fi
        rc=$?
        echo "RETRY($attempt, rc=$rc) $dst" >&2
        sleep $((attempt * 5))
    done
    echo "FAIL $dst" >&2
    return 1
}

fails=0
put "$STAGE/bundles/EVIDENCE_ARCHIVE_README.md"              "/$R/EVIDENCE_ARCHIVE_README.md" || fails=$((fails+1))
for b in characterization_pairs_localcpu characterization_profiles_math reports_profiles_cura optimization_evidence; do
    put "$STAGE/bundles/$b.tar.gz"        "/$R/repo_evidence/$b.tar.gz"        || fails=$((fails+1))
    put "$STAGE/bundles/$b.tar.gz.sha256" "/$R/repo_evidence/$b.tar.gz.sha256" || fails=$((fails+1))
done
put "$STAGE/bundles/branch_only_blobs.tar.gz"        "/$R/branch_evidence/branch_only_blobs.tar.gz"        || fails=$((fails+1))
put "$STAGE/bundles/branch_only_blobs.tar.gz.sha256" "/$R/branch_evidence/branch_only_blobs.tar.gz.sha256" || fails=$((fails+1))

for f in repo_evidence_manifest.sha256 kept_in_repo.txt bundle_summary.json \
         bundle_characterization_pairs_localcpu.txt bundle_characterization_profiles_math.txt \
         bundle_reports_profiles_cura.txt bundle_optimization_evidence.txt \
         branch_extraction_summary.json branch_handover_campaign-line_manifest.json \
         branch_perf_cpu-optimization_manifest.json branch_perf_native-optimization_manifest.json; do
    put "$STAGE/manifests/$f" "/$R/manifests/$f" || fails=$((fails+1))
done

for f in gitlog_handover_campaign-line.txt gitlog_perf_cpu-optimization.txt gitlog_perf_native-optimization.txt; do
    put "$STAGE/logs/$f" "/$R/logs/$f" || fails=$((fails+1))
done

echo "UPLOAD_FAILURES=$fails"
exit "$fails"
