"""Small diagnostic descriptors for ORIGINAL runtime-boundary values.

Call only from a separate diagnostic run. This helper does not install hooks,
change any project value or claim actual fast-path execution by itself.
"""
from __future__ import annotations
import json
import numpy as np


def describe(value):
    a=np.asarray(value)
    if a.dtype.hasobject: raise ValueError('Object data is outside this descriptor')
    kind='python_scalar' if type(value) in (int,float,bool,complex) else (
         'numpy_scalar' if isinstance(value,np.generic) else 'ndarray' if type(value) is np.ndarray else 'other')
    return {'python_kind':kind,'dtype':a.dtype.str,'shape':list(a.shape),'strides':list(a.strides),
            'ndim':a.ndim,'size':a.size,'is_singleton_array':kind=='ndarray' and a.ndim>0 and a.size==1,
            'c_contiguous':bool(a.flags.c_contiguous),
            'singleton_bits_hex':a.tobytes().hex() if a.size==1 else None}


def diagnose_types(named_values):
    return {'evidence_class':'runtime_descriptor_not_performance_measurement',
            'values':{name:describe(value) for name,value in named_values.items()},
            'limits':['This does not identify actual selected route; add counters at the real route/leaf seam.',
                      'No large field serialization, min/max scan or hidden dtype normalization.']}

if __name__=='__main__':
    print(json.dumps(diagnose_types({'example_air':np.float64(25.0),
                                   'example_wall':np.array([[12.0]],np.float32)}),indent=2))
