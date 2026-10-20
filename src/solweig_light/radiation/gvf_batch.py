"""Prepared GVF: compiled block ownership across all ordered directions.

Each block owns its receiver scratch, gathers with the existing serial ray
leaf, postprocesses float32 receivers with the original promoted Lup term,
and rounds each direction into float32 accumulators before moving on.
"""
import numpy as np
from numba import njit, prange
from .ground_view import _gather_block_serial
from .gvf_postprocess import _postprocess_pixel


@njit(cache=True, fastmath=False)
def _run_owner(owner, buildings, shadow, sunwall, lup_first, lup_rest, albshadow, alb,
         lwall, albedo, aspect, wallbol, lup_term, alb_term, nosh_term,
         schedules, lows, highs, modes, first, second, capacity, output):
    rows, cols = buildings.shape
    flagged = 0
    row0 = owner * capacity
    row1 = min(row0 + capacity, rows)
    size = row1 - row0
    block = np.empty((16, size, cols), np.float32)
    facesh = np.empty((size, cols), np.float32)
    gvf = np.empty((size, cols), np.float32)
    # Lup addition is promoted only after the f32 receiver arithmetic.
    gl = np.empty_like(lup_term[row0:row1])
    ga = np.empty((size, cols), np.float32)
    gn = np.empty((size, cols), np.float32)
    g2 = np.empty((size, cols), np.float32)
    for direction in range(len(schedules)):
        lup = lup_first if direction == 0 else lup_rest
        _gather_block_serial(row0, row1, buildings, shadow, sunwall,
                             lup, albshadow, alb, lwall, albedo,
                             schedules[direction], np.float32(first), block)
        low, high = lows[direction], highs[direction]
        for row in range(size):
            for col in range(cols):
                a = aspect[row0 + row, col]
                if modes[direction] == 0:
                    face = np.float32(a < low or a >= high)
                    facesh[row, col] = np.float32(np.float32(face - wallbol[row0+row,col]) + np.float32(1))
                else:
                    face = np.float32(a > low or a <= high)
                    facesh[row, col] = np.float32(np.float32(face * np.float32(-1)) + np.float32(1))
        for row in range(size):
            for col in range(cols):
                flagged += _postprocess_pixel(block, buildings[row0:row1],
                    facesh, lup_term[row0:row1], alb_term[row0:row1],
                    nosh_term[row0:row1], first, second, row, col,
                    gvf, gl, ga, gn, g2)
                # Each += has the baseline's float32 destination cast,
                # including the mixed f32 receiver / f64 Lup path.
                output[0,row0+row,col] = np.float32(output[0,row0+row,col] + gl[row,col])
                output[1,row0+row,col] = np.float32(output[1,row0+row,col] + ga[row,col])
                output[2,row0+row,col] = np.float32(output[2,row0+row,col] + gn[row,col])
                output[15,row0+row,col] = np.float32(output[15,row0+row,col] + g2[row,col])
                degrees = 5 + 20 * direction
                for cardinal in range(4):
                    selected = ((cardinal == 0 and degrees < 180) or
                                (cardinal == 1 and 90 <= degrees < 270) or
                                (cardinal == 2 and 180 <= degrees < 360) or
                                (cardinal == 3 and (270 <= degrees or degrees < 90)))
                    if selected:
                        at = 3 + 3 * cardinal
                        output[at,row0+row,col] = np.float32(output[at,row0+row,col] + gl[row,col])
                        output[at+1,row0+row,col] = np.float32(output[at+1,row0+row,col] + ga[row,col])
                        output[at+2,row0+row,col] = np.float32(output[at+2,row0+row,col] + gn[row,col])
    return flagged


@njit(cache=True, fastmath=False, parallel=True)
def _run(buildings, shadow, sunwall, lup_first, lup_rest, albshadow, alb,
         lwall, albedo, aspect, wallbol, lup_term, alb_term, nosh_term,
         schedules, lows, highs, modes, first, second, capacity, output):
    rows = buildings.shape[0]
    flagged = 0
    for owner in prange((rows + capacity - 1) // capacity):
        flagged += _run_owner(owner, buildings, shadow, sunwall, lup_first, lup_rest, albshadow, alb,
                lwall, albedo, aspect, wallbol, lup_term, alb_term, nosh_term,
                schedules, lows, highs, modes, first, second, capacity, output)
    return flagged


@njit(cache=True, fastmath=False)
def _finite_accumulators(output):
    """Scan all destination sums without allocating an isfinite mask.

    Finite per-direction postprocess results can overflow only when rounded
    into the float32 direction accumulators. Those events must also replay
    through NumPy to preserve warnings, raises, and nonfinite payload bits.
    """
    for component in range(output.shape[0]):
        for row in range(output.shape[1]):
            for col in range(output.shape[2]):
                if not np.isfinite(output[component,row,col]):
                    return False
    return True


def run(step, rows, cols, block_rows):
    """Return the 16 ordered accumulators, or None for retained execution.

    Non-default error regimes retain the original NumPy warning contract.
    A nonfinite compiled intermediate discards the private results and runs
    the original path, which reproduces its warnings from pristine inputs.
    """
    from numba.typed import List
    from .engine import _operate
    from .ground_view import _angular_constant, ray_schedule
    from .gvf_postprocess import _step_scalar
    if any(np.geterr()[key] not in ('warn','ignore') for key in ('divide','over','invalid')) or np.geterr()['under'] != 'ignore':
        return None
    if _step_scalar(step.first_steps) is None or _step_scalar(step.second_steps) is None:
        return None
    rasters = (step.buildings, step.shadow, step.sunwall, step.lup_first_snap,
        step.lup_rest_snap, step.albshadow, step.alb_grid, step.lwall,
        step.aspect, step.wallbol, step.alb_term, step.nosh_term)
    if ((rows,cols) != step.buildings.shape or
        any(a.shape != (rows,cols) or a.dtype != np.float32 for a in rasters)
        or step.lup_term.shape != (rows,cols)
        or step.lup_term.dtype not in (np.float32,np.float64)):
        return None
    schedules = List()
    lows, highs, modes = [], [], []
    for azimuth in step.azimuths:
        low = _operate(np.subtract, azimuth, _angular_constant(azimuth,np.pi/2))
        high = _operate(np.add, azimuth, _angular_constant(azimuth,np.pi/2))
        circle = _angular_constant(azimuth,2*np.pi)
        if low >= 0 and high < circle:
            mode = 0
        elif low < 0 and high <= circle:
            low = _operate(np.add,low,circle)
            mode = 1
        elif low > 0 and high >= circle:
            high = _operate(np.subtract,high,circle)
            mode = 1
        else:
            return None
        lows.append(low); highs.append(high); modes.append(mode)
        schedules.append(ray_schedule(step.buildings.shape,azimuth,step.scale,
                                       step.first_steps,step.second_steps))
    output = np.zeros((16,rows,cols),np.float32)
    flagged = _run(step.buildings, step.shadow, step.sunwall,
        step.lup_first_snap, step.lup_rest_snap, step.albshadow, step.alb_grid,
        step.lwall, np.float32(step.albedo_b), step.aspect, step.wallbol,
        step.lup_term, step.alb_term, step.nosh_term, schedules,
        np.asarray(lows),np.asarray(highs),np.asarray(modes),
        float(step.first_steps),float(step.second_steps),max(1,int(block_rows)),output)
    return None if flagged or not _finite_accumulators(output) else output
