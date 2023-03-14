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
    Algorithm to find trips of specific length using a given list of
    single-digit numbers.

    Rules to create a trip:
    - All numbers in the trip should be in the given list of numbers, except
        the last one, which should be 9.
    - The first 2 numbers can be any pair.
    - Starting from the third element, each number should be the ones digit of
        adding, subtracting, multiplying or dividing the previous 2 numbers.
    - Consider a trip like (...a,b,c,d,...) in which a,b,c,d are single digits.
        The d can be generated as the ones digit of b <> c where <> is
        (+ mod 10, - if valid, * mod 10, / if c divides b). We can also
        generate d by concatenating a and b into the 2-digit number ab and then
        using (ab - c) or (ab // c if c divides ab).

    Examples
    --------
    valid trips for [4,5,1,2,7,3,3,6]:
        413369 (4+1=3, 1*3=3, 3+3=6, 3+6=9)
        331459 (3/3=1, 3+1=4, 1+4=5, 4+5=9)
        431239 (4-3=1, 3-1=2, 1+2=3, 12-3=9)
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

    def run(self, jump_lengths=[6, 7, 8, 9]) -> typing.Dict[int, typing.List[str]]:
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

        log.info(f"num labels: {next(Label._id_gen)}")
        return jumps_by_length

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
    jumps_by_length = FindJumps(planet_nums).run()
    for length, jumps in jumps_by_length.items():
        log.info(f"{len(jumps)} jumps of length {length}:")
        for jump in jumps:
            log.info(f"\t{jump}")


if __name__ == '__main__':
    main()
