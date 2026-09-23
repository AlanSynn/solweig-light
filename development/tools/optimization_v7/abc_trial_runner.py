"""B7-31: exclusive A/B/C adapter comparison runner (performance owner).

Implements the frozen b7_03 protocol: independent child process per variant
configuration, effective-pool queries after init, alternating paired order,
non-overlapping boundaries (kernel-only / adapter-total), raw trial records.

Variant adapter contract (a small shim per variant maps its module to this):
    load_inputs(spec) -> inputs        # materialize the fixture in-child
    supported(inputs) -> bool          # pre-launch admission decision
    prepare(inputs) -> prepared        # packing/conversion (adapter boundary)
    kernel_only(prepared) -> out       # prepared -> sync -> host output
    adapter_total(inputs) -> out       # validate+prepare+invoke+sync+materialize
    identity() -> dict                 # backend/version/ISA/flags/pools

Every timed call re-runs prepare inside adapter_total so conversions are
counted; kernel_only times only prepared->sync->materialize. Outputs are
compared bitwise across variants by the parent after the run.

Usage:
  parent: python abc_trial_runner.py --config trials_config.json --out DIR
  child : python abc_trial_runner.py --worker SPEC.json   (internal)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHILD_MARKER = '--worker'


def worker_run(spec_path):
    """In-child: run one variant's paired repetitions over one boundary."""
    import importlib.util

    spec = json.loads(Path(spec_path).read_text())
    module_spec = importlib.util.spec_from_file_location('v7_adapter', spec['adapter'])
    adapter_module = importlib.util.module_from_spec(module_spec)
    sys.modules['v7_adapter'] = adapter_module
    module_spec.loader.exec_module(adapter_module)

    inputs = adapter_module.load_inputs(spec)
    record = {
        'variant': spec['variant'],
        'boundary': spec['boundary'],
        'reps': spec['reps'],
        'identity': adapter_module.identity(),
        'supported': adapter_module.supported(inputs),
        'samples_s': [],
        'output_bits_sha256': None,
        'rejected_reason': None,
    }
    if not record['supported']:
        record['rejected_reason'] = 'pre-launch admission rejected'
        return record
    import hashlib

    import numpy as np
    boundary = spec['boundary']
    for rep in range(spec['reps']):
        if boundary == 'kernel_only':
            prepared = adapter_module.prepare(inputs)  # untimed for this boundary
            start = time.perf_counter()
            output = adapter_module.kernel_only(prepared)
        elif boundary == 'adapter_total':
            start = time.perf_counter()
            output = adapter_module.adapter_total(inputs)
        else:
            raise ValueError(boundary)
        record['samples_s'].append(time.perf_counter() - start)
        if isinstance(output, np.ndarray):
            record['output_bits_sha256'] = hashlib.sha256(
                np.ascontiguousarray(output).view(np.uint8).tobytes()).hexdigest()
            record['output_shape'] = list(output.shape)
            record['output_dtype'] = str(output.dtype)
    record.pop('outputs', None)
    return record


def parent_run(config):
    """Alternate child invocations across variants; merge raw trials."""
    trials = []
    order = config['order']
    for round_index in range(config['rounds']):
        for variant in order:
            spec = dict(config['spec'])
            spec['variant'] = variant
            spec['adapter'] = config['adapters'][variant]
            spec['reps'] = config['reps']
            spec_path = Path(config['out']) / f'spec_r{round_index}_{variant}.json'
            spec_path.write_text(json.dumps(spec))
            result = subprocess.run(
                [sys.executable, __file__, CHILD_MARKER, str(spec_path)],
                capture_output=True, text=True, env=worker_env(config.get('env', {})))
            if result.returncode != 0:
                trials.append({'variant': variant, 'round': round_index,
                               'error': result.stderr[-2000:]})
                continue
            record = json.loads(result.stdout.splitlines()[-1])
            record['round'] = round_index
            trials.append(record)
    return trials


def worker_env(extra):
    env = dict(os.environ)
    env.update(extra)
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config')
    parser.add_argument('--out')
    parser.add_argument(CHILD_MARKER, dest='worker')
    args = parser.parse_args()
    if args.worker:
        record = worker_run(args.worker)
        print(json.dumps(record))
        return
    config = json.loads(Path(args.config).read_text())
    config['out'] = args.out or config.get('out', '.')
    Path(config['out']).mkdir(parents=True, exist_ok=True)
    trials = parent_run(config)
    output_path = Path(config['out']) / f"trials_{config['spec'].get('label', 'run')}.json"
    output_path.write_text(json.dumps({
        'schema': 'solweig-v7-abc-trials-v1',
        'config': {key: value for key, value in config.items() if key != 'spec'},
        'spec_boundary': config['spec'].get('boundary'),
        'trials': trials,
    }, indent=1))
    print('written', output_path)


if __name__ == '__main__':
    main()
