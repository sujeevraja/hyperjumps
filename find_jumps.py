#!/usr/bin/env python

import heapq
import itertools
import logging
import typing

log = logging.getLogger(__name__)


class Label:
    _id_gen = itertools.count()

    def __init__(self, seq: str, nums_left: typing.List[int]):
        self.id: int = next(self._id_gen)
        self.seq: str = seq
        self.nums_left: str = nums_left

    def __lt__(self, other: 'Label') -> bool:
        """This operator serves to prioritize label in a min-priority-queue."""
        # Labels with longer sequences should be better.
        if len(self.seq) != len(other.seq):
            return len(self.seq) > len(other.seq)

        return self.id < other.id

    def __repr__(self) -> str:
        return f"Label({self.id},{self.seq},{self.nums_left})"

    @classmethod
    def reset_id(cls):
        cls._id_gen = itertools.count()

    def extend(self, num_str: str) -> typing.Optional['Label']:
        """Prepone num_str to self.seq."""
        nums = list(map(int, num_str))
        nums_left = [n for n in self.nums_left]
        for num in nums:
            try:
                nums_left.remove(num)
            except ValueError:
                return None

        return Label(f"{num_str}{self.seq}", nums_left)


def build_initial_labels(nums: typing.List[int]) -> typing.List[Label]:
    labels = []
    for n in set(nums):
        seq = f"{n}9"
        nums_left = [p for p in nums]
        nums_left.remove(n)
        labels.append(Label(seq, nums_left))

    return labels


def can_reach(p: int, q: int, r: int) -> bool:
    if (p+q) % 10 == r or (p*q) % 10 == r:
        return True

    if p >= q:
        if ((p-q) % 10) == r:
            return True

        if p % q == 0 and p // q == r:
            return True

    return False


class FindJumps:
    """
    Create a sequence of single-digit numbers with the following rules:
    - The first 2 elements of the sequence should be from `planet_nums`.
    - The sequence should end with 9.
    - The length of the sequence should be `jump_length`.
    - Starting from the third element, each number should be the ones digit of
        adding, subtracting, multiplying or dividing the previous 2 numbers.
    - Consider a sequence like a_1, a_2, a_3, ... a_k in which a_i is a single
        digit. a_{k+1} can be generated as the ones digit of a_{k-1} <> a_k
        where <> can be any of (add, subtract, multiply or divide).
    - a_{k+1} can also be generated as b <> _k where b is formed by
        selecting a continuous subsequence starting at a_m for 1 <= m < k
        partitining it into (a_m,...,a_n), (a_{n+1},...,a_k) and concatenating
        these 2 sub-sequences to create the multi-digit numbers b and c.
    - In other words, if you're trying a new number z for the sequence by doing
        x <> y, then y must be a single digit but x can be multiple digits.

    Examples
    --------
    input: [4,5,1,2,7,3,3,6]
    sequences:
        [4,1,3,3,6,9] (4+1=3, 1*3=3, 3+3=6, 3+6=9)
        [4,3,1,2,3,9] (4-3=1, 3-1=2, 1+2=3, 12-3=9)
        [3,3,1,4,5,9] (3/3=1, 3+1=4, 1+4=5, 4+5=9)

        The 4,3,1,2,3,9 case is an interesting example.
        It needs 1+2=3 and 12-3=9 to hold. How to capture this in a graph?
        Say my graph has x -- (y) --> d if x<>y == d.
        Then, the graph would have 1 --(+2)--> 3 and (12) --(-3)--> 9.
        What should the graph store?

        Let's try the simple approach in which nodes are digits, edges are
        operators (+,-,*,/,==).

        1 -(+)-> 2 --(==)--> 3
        12 --(-)--> 3 --(==)--> 9

        Nah, too complicated.

        Say we go backwards from 9.
        We need to find pairs like x,y such that
            x-y == 9, x+y == 9, x*y == 9, x/y == 9, or
            x == 9+y, x == 9-y, x == 9/y, x == 9*y.
            If x has 2 digits (say ab), then there is the additional constraint
            that a<>b == y.

        Perhaps we don't need to build the graph at all.
        Start with a DFS going backwards from 9, with edges just meaning that
        we can get to a digit.

    Valid sequence examples:
        Label(15,[9, 3, 2, 1, 3, 4],[5, 7, 6])
        Label(20,[9, 3, 3, 1, 4, 5],[2, 7, 6])
        Label(27,[9, 4, 3, 1, 2, 3],[5, 7, 6])
        Label(33,[9, 5, 4, 1, 3, 3],[2, 7, 6])


    UPDATE: These are found by the latest algo. They weren't found by the
    previous version of the algo.
    For the sequence [1, 2, 3, 3, 4, 4, 6, 8], here are the results for this
    algo:
    # 441339 (found)
    # 312369 (found)
    # 413369 (found)
    # 431239 (found)
    # 4413369 (found)
    # 8441339 (found)
    # 8312369 (not found)
    # 84413369 (found)
    # 68441339 (not found)
    # 286441339 (not found)

    Issue can be illustrated with 8312369. When we backtrack from (3,1...), we
    can't figure out that 8 can added to the front as 8+3 == 11.
    """

    def __init__(self, planet_nums: typing.List[int]):
        self.planet_nums: typing.List[int] = planet_nums
        self._unique_nums = set(planet_nums)
        self._num_counts = {}
        for n in planet_nums:
            self._num_counts[n] = self._num_counts.get(n, 0) + 1

        # keys are of the form "ab" and values are single digits c such that
        # (c <> a) % 10 == b for <> \in {+,-,*,/}.
        self._cache1 = {}

        # keys are of the form "ab" and values are 2-digit strings of the form
        # cd such that c <> d == a and (cd - a == b) or (cd / a) == b.
        self._cache2 = {}

    def run(self, jump_lengths: typing.List[int]):
        """
        Given a digit seq like (ab...), look for the following:

        case 1: ca -> b (e.g. 63 -> 9)
        case 2: cd -> a, cd - a -> b (e.g. 12 -> 3 -> 9)
        case 3: cd -> a, cd / a -> b (e.g. 12 -> 3 -> 4)

        Let's stick to just 2-digit numbers for now. Note that the case
        dc -> a, ca -> b is covered by case 1; we would find ca -> b, then
        extend the label in the next iteration by finding dc -> a.
        """
        h = []
        for label in build_initial_labels(self.planet_nums):
            heapq.heappush(h, label)

        jumps_by_length = {l: set() for l in jump_lengths}
        while h:
            label = heapq.heappop(h)
            for ext in self._extend1(label):
                if len(ext.seq) in jumps_by_length:
                    jumps_by_length[len(ext.seq)].add(ext.seq)
                heapq.heappush(h, ext)
            for ext in self._extend2(label):
                if len(ext.seq) in jumps_by_length:
                    jumps_by_length[len(ext.seq)].add(ext.seq)
                heapq.heappush(h, ext)

        for length, jumps in jumps_by_length.items():
            log.info(f"jumps of length {length}")
            for jump in jumps:
                log.info(f"\t{jump}")

        log.info(f"num labels: {next(Label._id_gen)}")

    def _extend1(self, label: Label) -> typing.Generator[Label, None, None]:
        """
        Given a sequence starting with (ab...), find c such that ca -> b.
        """
        ab = label.seq[:2]
        if ab not in self._cache1:
            self._update_cache1(ab)

        for c in self._cache1[ab]:
            ext = label.extend(str(c))
            if ext:
                yield ext

    def _update_cache1(self, ab: str):
        """
        Given a sequence starting with (ab...), find c such that ca -> b.
        """
        a, b = map(int, ab)
        candidates = []

        for c in self._unique_nums:
            if ((c == a or c == b) and self._num_counts[c] == 1):
                continue

            if can_reach(c, a, b):
                candidates.append(c)

        self._cache1[ab] = candidates

    def _extend2(self, label: Label) -> typing.Generator[Label, None, None]:
        """
        Given a sequence starting with (ab...), find cd such that
         c <> d == a and (cd - a == b or cd / a == b).
        """
        ab = label.seq[:2]
        if ab not in self._cache2:
            self._update_cache2(ab)

        for cd in self._cache2[ab]:
            ext = label.extend(cd)
            if ext:
                yield ext

    def _update_cache2(self, ab: str):
        a, b = map(int, ab)

        # First find cd such that c <> d == a.
        # Look for entries of (d,a) in self._cache1.
        nums = [n for n in self.planet_nums]
        nums.remove(a)
        if b != 9:
            nums.remove(b)

        candidates = []
        for d in nums:
            da = f"{d}{a}"
            if da not in self._cache1:
                self._update_cache1(da)

            # Look for cd such that cd - a == b or cd // a == b.
            for c in self._cache1[da]:
                cd = (10*c) + d
                if ((cd - a) % 10 == b) or (cd % a == 0 and cd // a == b):
                    candidates.append(str(cd))

        self._cache2[ab] = candidates


def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)
    # planet_nums = [8, 7, 7, 4, 8, 1, 3, 8]
    # planet_nums = [4, 5, 1, 2, 7, 3, 3, 6]
    # planet_nums = [1, 2, 3, 3, 4, 4, 6, 8]
    planet_nums = [7, 1, 8, 3, 3, 8, 1, 4]
    jump_lengths = [6, 7, 8, 9]
    FindJumps(planet_nums).run(jump_lengths)


if __name__ == '__main__':
    main()
