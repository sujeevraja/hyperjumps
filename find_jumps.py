#!/usr/bin/env python

import heapq
import itertools
import logging
import operator
import typing

log = logging.getLogger(__name__)


class Label:
    _id_gen = itertools.count()

    def __init__(self, seq: typing.List[int], nums_left: typing.List[int]):
        self.id: int = next(self._id_gen)
        self.seq: typing.List[int] = seq
        self.nums_left: typing.List[int] = nums_left

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


def extend(label: Label, nums: typing.List[int]) -> typing.Optional[Label]:
    seq = [s for s in label.seq]
    left = [l for l in label.nums_left]

    for num in nums:
        seq.append(num)

        # This exception handling ensures that we don't consider removing too
        # many copies of a number as valid.
        try:
            left.remove(num)
        except ValueError:
            return None

    return Label(seq=seq, nums_left=left)


def can_reach(p: int, q: int, r: int) -> bool:
    if (p+q) % 10 == r or (p*q) % 10 == r:
        return True

    if p > q:
        if ((p-q) % 10) == r:
            return True

        if p % q == 0 and p // q == r:
            return True

    return False


def extensions(label: Label) -> typing.Generator[Label, None, None]:
    oprs = [operator.add, operator.sub, operator.mul, operator.floordiv]
    x = label.seq[-2]
    y = label.seq[-1]

    for opr in oprs:
        z = opr(x, y)
        if z <= 9:
            if z in label.nums_left:
                ext = extend(label, [z])
                if ext:
                    yield (ext)
            continue

        # Yes, there is a betteer way to do this with divs and mods. But
        # I'm using this as a hack to get to finding jumps quickly.
        digits = list(map(int, str(z)))

        # Let's ignore (3 or more)-digit cases for now as they seem be be
        # quite rare.
        if len(digits) > 2:
            continue

        # Ensure that all digits of the multi-digit result are valid.
        if any([d not in label.nums_left for d in digits]):
            continue

        a, b = digits

        # For example, if we want to use 9+3 == 12, then, all digits 3,1,2
        # should be valid. Further, as we did 9 <> 3 to get to 12, we
        # should also check that 3 <> 2 == 1.
        # Here, the label's sequence may look like [...,x,y] with x<>y == z and
        # z is a 2-digit number ab. We want a<>b == y and (ab)<>y == x. The
        # second condition is guaranteed by symmetry of (+,-) and (*,/). The
        # first condition needs to be checked here.
        if can_reach(a, b, y):
            ext = extend(label, [b, a])
            if ext:
                yield (ext)


def build_initial_labels(planet_nums: typing.List[int]) -> typing.List[Label]:
    labels = []
    first_label = Label(seq=[9], nums_left=planet_nums)
    for num in set(planet_nums):
        labels.append(extend(first_label, [num]))
    return labels


def algo1(planet_nums: typing.List[int], jump_length: int):
    """
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
    labels = build_initial_labels(planet_nums)
    h = []
    for label in labels:
        heapq.heappush(h, label)

    built_seqs = []
    while h:
        label = heapq.heappop(h)
        for ext in extensions(label):
            if len(ext.seq) == jump_length:
                seq = list(reversed(ext.seq))
                if seq not in built_seqs:
                    built_seqs.append(seq)
                    seq_str = ''.join(map(str, seq))
                    print(ext.id, seq_str)
            else:
                heapq.heappush(h, ext)
                seq = list(reversed(ext.seq))
                # 8312369
                # if seq == [3, 1, 2, 3, 6, 9]:
                #     log.info(f"adding {ext}")


def run(planet_nums: typing.List[int], jump_length: int, num_seqs: int):
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
    """
    algo1(planet_nums, jump_length)


def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)

    # planet_nums = [8, 7, 7, 4, 8, 1, 3, 8]
    planet_nums = [4, 5, 1, 2, 7, 3, 3, 6]
    lengths_and_counts = [
        (6, 4),
        (7, 3),
        (8, 2),
        (9, 1),
    ]
    for jump_length, num_seqs in lengths_and_counts:
        log.info(f"trying to get {num_seqs} seqs of length {jump_length}")
        run(planet_nums, jump_length, num_seqs)
        log.info(f"num labels: {next(Label._id_gen)}")
        Label.reset_id()


if __name__ == '__main__':
    main()
