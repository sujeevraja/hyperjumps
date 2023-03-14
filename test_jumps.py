#!/usr/bin/env python

import find_jumps as fj
import unittest


class TestJumps(unittest.TestCase):
    def test_reachability(self):
        """Test common ways in which `can_reach` is used."""
        self.assertTrue(fj.can_reach(1, 2, 3))  # simple addition
        self.assertTrue(fj.can_reach(8, 7, 5))  # addition mod 10
        self.assertTrue(fj.can_reach(8, 4, 4))  # subtraction
        self.assertTrue(fj.can_reach(12, 4, 8))  # 2-digit subtraction
        self.assertTrue(fj.can_reach(8, 7, 6))  # multiplication mod 10
        self.assertTrue(fj.can_reach(4, 4, 1))  # division by itself
        self.assertTrue(fj.can_reach(12, 4, 3))  # 2-digit division

    def test_jump_seq_1(self):
        """This case was found online. Trips in this problem helped rebuild and
        refine the algorithm."""
        trips_by_length = fj.FindJumps([1, 2, 3, 3, 4, 4, 6, 8]).run()
        for trip in ["441339", "312369", "413369", "431239"]:
            self.assertTrue(trip in trips_by_length[6])

        for trip in ["4413369", "8441339", "8312369"]:
            self.assertTrue(trip in trips_by_length[7])

        for trip in ["84413369", "68441339"]:
            self.assertTrue(trip in trips_by_length[8])

        self.assertTrue("286441339" in trips_by_length[9])


if __name__ == '__main__':
    unittest.main()
