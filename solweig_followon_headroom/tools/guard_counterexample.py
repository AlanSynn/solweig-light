"""Local correctness counterexample only; not a SOLWEIG or Slurm benchmark."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def demonstrate() -> dict:
    with tempfile.TemporaryDirectory(prefix='fingerprint-proof-') as root:
        path = Path(root) / 'input.bin'
        path.write_bytes(b'AAAA')
        before = path.stat()
        key_before = (str(path), before.st_mtime_ns, before.st_size)
        old = hashlib.sha256(path.read_bytes()).hexdigest()
        # Modify in place, retain inode and length; restore original mtime.
        with path.open('r+b') as f:
            f.write(b'BBBB')
            f.flush()
            os.fsync(f.fileno())
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = path.stat()
        key_after = (str(path), after.st_mtime_ns, after.st_size)
        new = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            'evidence_class': 'executed_local_stdlib_counterexample',
            'same_path_mtime_size_key': key_before == key_after,
            'same_inode': before.st_ino == after.st_ino,
            'content_hash_changed': old != new,
            'old_sha256': old,
            'new_sha256': new,
            'conclusion': 'path/mtime/size caching cannot preserve full-content mutation detection',
            'solweig_executed': False,
            'target_host_executed': False,
        }


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    out = json.dumps(demonstrate(), indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(out)
    else:
        print(out, end='')
