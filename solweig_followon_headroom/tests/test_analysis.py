import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from floor_model import Chain, stage_speedup, max_nonaccelerated_fraction, admissible_shapes, report
from guard_counterexample import demonstrate


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.c = Chain(20, 4063.1, 2529.7, 24, 24)

    def test_supplied_sum(self):
        self.assertAlmostEqual(self.c.total_s, 6612.8)

    def test_zero_svf_floor(self):
        self.assertAlmostEqual(self.c.scenario(math.inf)['total_s'], 2549.7)

    def test_fivefold_svf(self):
        self.assertAlmostEqual(self.c.scenario(5)['total_s'], 3362.32)

    def test_sevenfold_svf(self):
        self.assertAlmostEqual(self.c.scenario(7)['total_s'], 3130.142857142857)

    def test_run_required_after_g5(self):
        self.assertAlmostEqual(self.c.scenario(5)['run_speedup_required_for_target'], 2.6150013438359276)

    def test_run_required_after_elimination(self):
        self.assertAlmostEqual(self.c.scenario(math.inf)['run_speedup_required_for_target'], 1.4211797752808988)

    def test_infeasible_even_zero_run_at_g2(self):
        self.assertFalse(self.c.scenario(2)['run_target_feasible_with_fixed_svf'])

    def test_amdahl_whole_stage(self):
        self.assertAlmostEqual(stage_speedup(.2, 8), 10 / 3)

    def test_nonaccelerated_threshold(self):
        self.assertAlmostEqual(max_nonaccelerated_fraction(5, 8), .08571428571428572)
        self.assertAlmostEqual(max_nonaccelerated_fraction(7, 8), .020408163265306114)

    def test_impossible_threshold(self):
        self.assertIsNone(max_nonaccelerated_fraction(9, 8))

    def test_no_acceleration_for_full_residual(self):
        self.assertEqual(stage_speedup(1, 8), 1)

    def test_monotone_horizon_gain(self):
        a = self.c.linear_time_envelope(1, 7)
        b = self.c.linear_time_envelope(72, 7)
        self.assertGreater(a['speedup'], b['speedup'])

    def test_hypothesis_labeled(self):
        self.assertEqual(self.c.linear_time_envelope(72, 7)['evidence_class'], 'hypothetical_average_step_sensitivity')

    def test_invalid_inputs(self):
        for a in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                Chain(a, 1, 1, 24, 24)
        with self.assertRaises(ValueError):
            self.c.scenario(0)
        with self.assertRaises(ValueError):
            self.c.linear_time_envelope(0)
        with self.assertRaises(ValueError):
            stage_speedup(1.1, 8)

    def test_capacity_uses_threads(self):
        shapes = admissible_shapes(24, 24, 1000, 100, {1: 100, 8: 150})
        self.assertTrue(all(x['native_threads'] <= 24 for x in shapes))
        self.assertTrue(all(x['charged_bytes'] <= 1000 for x in shapes))
        self.assertTrue(all(x['workers'] <= 3 for x in shapes if x['threads_per_worker'] == 8))

    def test_capacity_is_not_speed_evidence(self):
        for x in admissible_shapes(8, 4, 100, 10, {1: 20, 4: 30}):
            self.assertEqual(x['status'], 'capacity_admissible_not_timed')

    def test_report_serializes_without_nonfinite(self):
        r = report()
        json.dumps(r, allow_nan=False)
        self.assertFalse(r['new_solweig_measurements'])
        self.assertEqual(r['actual_target_status'], 'unverified')

    def test_metadata_hash_guard_counterexample(self):
        r = demonstrate()
        self.assertTrue(r['same_path_mtime_size_key'])
        self.assertTrue(r['same_inode'])
        self.assertTrue(r['content_hash_changed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
