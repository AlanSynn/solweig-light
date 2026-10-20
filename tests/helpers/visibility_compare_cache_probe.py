"""Isolated native verifier probe for same-stamp persistent-cache upgrades."""
import argparse
import json

import numpy as np

from solweig_light.geometry.visibility import PackedVisibility
from solweig_light.geometry.visibility_compiled import compare_block_bits, _compare_bits


parser = argparse.ArgumentParser()
parser.add_argument('--mode')
parser.add_argument('--order')
parser.add_argument('--result', required=True)
args = parser.parse_args()
actual = np.ones((1, 4, 3), np.float32)
channel = PackedVisibility.from_dense(actual)
assert channel.modes == ('binary',)*3
result = compare_block_bits(channel, actual.reshape(4, 3).view(np.uint32), 0, 4, 3)
with open(args.result, 'w') as output:
    json.dump({'result': result, 'qualname': _compare_bits.py_func.__qualname__}, output)
