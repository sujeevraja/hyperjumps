#!/usr/bin/env python

import find_jumps as fj
import unittest


class TestJumps(unittest.TestCase):
    def test_reachability(self):
        """Test common ways in which `can_reach` is used."""
        self.assertTrue(fj.can_reach(1, 2, 3))  # simple addition
        self.assertTrue(fj.can_reach(8, 7, 5))  # addition mod 10
        self.assertTrue(fj.can_reach(8, 4, 4))  # subtraction
        self.assertTrue(fj.can_reach(8, 7, 6))  # multiplication mod 10
        self.assertTrue(fj.can_reach(4, 4, 1))  # division by itself

    def test_jump_seq_1(self):
        trips_by_length = fj.find_trips(nums=[1, 2, 3, 3, 4, 4, 6, 8], target=9)
        print(trips_by_length)
        expected_trips_by_length = {
            4: ['2369', '3369', '1339', '6339', '3819'],
            5: ['13369', '12369', '21339', '41339', '63819'],
            6: ['213369', '413369', '312369', '441339'],
            7: ['4413369', '4312369', '8312369', '6441339', '8441339'],
            8: ['84413369', '68441339', '86441339'],
            9: ['268441339', '286441339']}
        
        self.assertEqual(
            trips_by_length.keys(),
            expected_trips_by_length.keys())
        for size in trips_by_length:
            actual = set(trips_by_length[size])
            expected = set(expected_trips_by_length[size])
            self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
