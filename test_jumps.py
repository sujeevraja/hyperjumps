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


if __name__ == '__main__':
    unittest.main()
