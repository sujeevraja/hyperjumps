#!/usr/bin/env python

import argparse
import itertools
import logging
import typing

log = logging.getLogger(__name__)


class Config(typing.NamedTuple):
    """Script configuration.

    Attributes:
        nums: numbers from which sequence is to be generated.
        target: Digit of final planet to reach.
    """
    nums: typing.List[int]
    target: int


class Trip:
    _id_gen = itertools.count()

    def __init__(self, seq: str, nums_left: typing.List[int]):
        self.id: int = next(self._id_gen)
        self.seq: str = seq
        self.nums_left: typing.List[int] = nums_left

    def __repr__(self) -> str:
        return f"Trip(id={self.id},seq={self.seq},left={self.nums_left})"

    @classmethod
    def reset_id(cls):
        cls._id_gen = itertools.count()
    
    @property
    def size(self) -> int:
        return len(self.seq)
    
    def prefix(self, num: int) -> typing.Optional['Trip']:
        nums_left = [n for n in self.nums_left]
        try:
            nums_left.remove(num)
        except ValueError:
            return None
        
        return Trip(f"{num}{self.seq}", nums_left)


def build_initial_trips(
        nums: typing.List[int], target: int) -> typing.List[Trip]:
    trips = []
    for n in set(nums):
        seq = f"{n}{target}"
        nums_left = [p for p in nums]
        nums_left.remove(n)
        trips.append(Trip(seq, nums_left))
    return trips


def can_reach(first: int, second: int, result: int) -> bool:
    if (first+second) % 10 == result or (first*second) % 10 == result:
        return True

    if first >= second:
        if ((first-second) % 10) == result:
            return True

        if first % second == 0 and first // second == result:
            return True

    return False


def find_counts(nums: typing.List[int]) -> typing.Dict[int, int]:
    """ Return the frequency distribution of numbers in `nums`.

    Args:
        nums: List of numbers to find frequency distribution with.
    
    Returns:
        dict: A dict with keys as numbers in `nums` and values as the number
        of times the key occurs in `nums`.
    """
    num_counts = {}
    for n in nums:
        num_counts[n] = num_counts.get(n, 0) + 1
    return num_counts


class NumInfo(typing.NamedTuple):
    nums: typing.List[int]
    target: int
    unique_nums: typing.Set[int] = set()
    num_counts: typing.Dict[int, int] = {}

    @classmethod
    def build(cls, nums: typing.List[int], target: int) -> 'NumInfo':
        num_info = cls(
            nums=nums,
            target=target,
            unique_nums=set(nums),
            num_counts=find_counts(nums),
        )
        return num_info

    def counts_valid(self, given_nums: typing.List[int]) -> bool:
        counts = find_counts(given_nums)
        for n, count in counts.items():
            if n != self.target and self.num_counts[n] < count:
                return False
        return True


def num_pairs(nums: typing.List[int], target) -> typing.Generator:
    for n in nums:
        yield n, target

    for a, b in itertools.permutations(nums, 2):
        yield a, b


def compute_cab_cache(info: NumInfo) -> typing.Dict[str, typing.List[int]]:
    """
    Collect c such that c <> a == b for single-digit numbers a,b,c and
    <> in {+, - iff c > a, *, / if a divides c}.

    Store them in a dict with keys as "ab" strings.
    """
    cache = {}
    for a, b in num_pairs(info.nums, info.target):
        candidates = []
        for c in info.unique_nums:
            if ((c == a or c == b) and c not in info.num_counts):
                continue

            if can_reach(c, a, b) and info.counts_valid([a, b, c]):
                candidates.append(c)

        if candidates:
            cache[f"{a}{b}"] = candidates

    return dict(sorted(cache.items()))


def find_trips(
        nums: typing.List[int],
        target: int,
        min_trip_length: int = 4,
) -> typing.Dict[int, typing.Set[str]]:
    """
    Algorithm to find trips of specific length using a given list of
    single-digit numbers.

    Rules to create a trip:
    - All numbers in the trip should be in the given list of numbers, except
        the last one, which should be the target.
    - The first 2 numbers can be any pair.
    - Starting from the third element, each number should be the ones digit of
        adding, subtracting, multiplying or dividing the previous 2 numbers.

    Examples:
        valid trips for [4,5,1,2,7,3,3,6]:
            413369 (4+1=3, 1*3=3, 3+3=6, 3+6=9)
            331459 (3/3=1, 3+1=4, 1+4=5, 4+5=9)
            431239 (4-3=1, 3-1=2, 1+2=3, 12-3=9)
    """
    cache = compute_cab_cache(NumInfo.build(nums=nums, target=target))
    log.info("jump cache")
    num_jumps = 0
    for ab, jumps in cache.items():
        a, b = ab
        log.info(f"\t{jumps} <> {a} == {b}")
        num_jumps += len(jumps)
    log.info(f"num jumps found: {num_jumps}")

    trips_by_length = {}
    trips = build_initial_trips(nums, target)
    while trips:
        trip = trips.pop()
        log.info(f"trip {trip}")
        ab: str = trip.seq[:2]
        for jump in cache.get(ab, []):
            ext = trip.prefix(jump)
            if ext:
                trips.append(ext)
                if ext.size >= min_trip_length:
                    if ext.size not in trips_by_length:
                        trips_by_length[ext.size] = []
                    trips_by_length[len(ext.seq)].append(ext.seq)

    log.info(f"num trips: {next(Trip._id_gen)}")
    return trips_by_length


def run(cfg: Config):
    trips_by_length = find_trips(cfg.nums, cfg.target)
    for length, trips in trips_by_length.items():
        log.info(f"{len(trips)} trips of length {length}")
        for trip in trips:
            log.info(f"\t{trip}")


def handle_command_line():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    with open("planet_numbers.txt", "r") as infile:
        default_nums, target = next(infile).strip().split(",")

    parser.add_argument(
        "-n", "--nums", type=str, default=default_nums,
        help="digits from which trips are to be found")

    parser.add_argument(
        "-t", "--target", type=int, default=target,
        help = "digit of final target to reach")

    args = parser.parse_args()
    return Config(nums=[int(c) for c in args.nums], target=args.target)


def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)
    cfg = handle_command_line()
    run(cfg)


if __name__ == '__main__':
    main()
